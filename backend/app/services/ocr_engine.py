import os
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_use_onednn'] = '0'
# Restrict CPU thread usage of PaddlePaddle / OpenMP / MKL to prevent overheating
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import io
from pathlib import Path
from typing import Any
from fastapi import UploadFile
from PIL import Image
import numpy as np
import fitz  # PyMuPDF
import cv2

try:
    from paddleocr import PaddleOCR
except ImportError:
    # Fallback to dummy class if not installed yet during bootstrap
    PaddleOCR = None

from .documents import save_upload


_worker_ocr = None

def _init_ocr_worker() -> None:
    global _worker_ocr
    # Restrict CPU thread usage of PaddlePaddle / OpenMP / MKL inside the worker
    import os
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    
    from paddleocr import PaddleOCR
    _worker_ocr = PaddleOCR(
        ocr_version='PP-OCRv4',
        use_textline_orientation=False,
        use_doc_unwarping=False,
        use_doc_orientation_classify=False,
        lang="en",
        enable_mkldnn=False
    )


def _preprocess_image(img: np.ndarray) -> np.ndarray:
    # 1. Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    
    # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # 3. Bilateral Filter for Denoising
    denoised = cv2.bilateralFilter(enhanced, 9, 75, 75)
    
    # 4. Deskewing
    try:
        thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) > 0:
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            if abs(angle) > 0.5 and abs(angle) < 15:
                (h, w) = img.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                denoised = cv2.warpAffine(denoised, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    except Exception:
        pass
        
    processed_rgb = cv2.cvtColor(denoised, cv2.COLOR_GRAY2RGB)
    return processed_rgb


def _parse_ocr_result(ocr_result) -> list[dict[str, Any]]:
    parsed = []
    if not ocr_result or not ocr_result[0]:
        return parsed
    
    res = ocr_result[0]
    if isinstance(res, dict):
        texts = res.get("rec_texts", [])
        confs = res.get("rec_confs", [])
        polys = res.get("dt_polys", [])
        for i in range(len(texts)):
            text = str(texts[i])
            conf = float(confs[i]) if i < len(confs) else 0.8
            box = polys[i] if i < len(polys) else []
            parsed.append({"text": text, "box": box, "confidence": conf})
    else:
        for line in res:
            if line and len(line) > 1 and line[1]:
                text = str(line[1][0])
                conf = float(line[1][1])
                box = line[0]
                parsed.append({"text": text, "box": box, "confidence": conf})
    return parsed


def _re_ocr_low_confidence_lines(img: np.ndarray, lines: list[dict[str, Any]], ocr_client) -> list[dict[str, Any]]:
    h_img, w_img = img.shape[:2]
    for line in lines:
        if line["confidence"] < 0.90 and line["box"] is not None and len(line["box"]) > 0:
            try:
                box = np.array(line["box"], dtype=np.int32)
                x, y, w, h = cv2.boundingRect(box)
                pad = 8
                x1 = max(0, x - pad)
                y1 = max(0, y - pad)
                x2 = min(w_img, x + w + pad)
                y2 = min(h_img, y + h + pad)
                
                crop = img[y1:y2, x1:x2]
                if crop.size > 0:
                    crop_res = ocr_client.ocr(crop, det=False)
                    if crop_res and crop_res[0] and crop_res[0][0]:
                        text, conf = crop_res[0][0]
                        if conf > line["confidence"]:
                            line["text"] = str(text)
                            line["confidence"] = float(conf)
            except Exception:
                pass
    return lines


def _ocr_page_task(pdf_path: str, page_num: int) -> dict[str, Any]:
    global _worker_ocr
    import fitz
    from PIL import Image
    import numpy as np
    
    # 1. Load document and page
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    
    # 2. Render page at 350 DPI (Optimal resolution for legal documents/scans)
    zoom = 350 / 72
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img_np = np.array(image)
    
    # 3. Apply Preprocessing
    processed_img = _preprocess_image(img_np)
    
    # 4. Ensure OCR client is initialized inside the worker
    if _worker_ocr is None:
        _init_ocr_worker()
    
    # 5. Perform OCR
    ocr_result = _worker_ocr.ocr(processed_img)
    
    # 6. Parse results
    lines = _parse_ocr_result(ocr_result)
    
    # 7. Low-confidence Crop Re-OCR
    lines = _re_ocr_low_confidence_lines(processed_img, lines, _worker_ocr)
    
    avg_conf = np.mean([l["confidence"] for l in lines]) if lines else 0.0
    
    return {
        "page_number": page_num,
        "lines": lines,
        "width": pix.width,
        "height": pix.height,
        "confidence": float(avg_conf)
    }


class OCREngine:
    def __init__(self) -> None:
        self._ocr = None

    @property
    def ocr_client(self) -> Any:
        if self._ocr is None:
            if PaddleOCR is not None:
                # Initialize CPU-based PaddleOCR quietly, skipping heavy layout/unwarping models
                try:
                    self._ocr = PaddleOCR(
                        ocr_version='PP-OCRv4',
                        use_textline_orientation=False,
                        use_doc_unwarping=False,
                        use_doc_orientation_classify=False,
                        lang="en",
                        enable_mkldnn=False
                    )
                except Exception:
                    # Fallback for older PaddleOCR versions that don't support new pipeline parameters
                    self._ocr = PaddleOCR(use_angle_cls=True, lang="en", enable_mkldnn=False)
            else:
                class DummyOCR:
                    def ocr(self, *args, **kwargs):
                        return []
                self._ocr = DummyOCR()
        return self._ocr

    def extract_text_from_pdf(self, pdf_path: Path) -> dict[str, str]:
        results: dict[str, str] = {}
        pdf_path = Path(pdf_path)

        doc = fitz.open(str(pdf_path))
        
        # 1. Identify scanned pages that need OCR
        pages_to_ocr = []
        for i, page in enumerate(doc):
            page_num = i + 1
            text = page.get_text("text").strip()
            if text:
                results[f"page_{page_num}"] = text
            else:
                pages_to_ocr.append(page_num)

        # 2. Run OCR in parallel using ProcessPoolExecutor if there are pages to OCR
        if pages_to_ocr:
            from concurrent.futures import ProcessPoolExecutor
            # On Windows, ProcessPoolExecutor with PaddlePaddle/PaddleOCR is prone to deadlocks/hangs.
            if os.name == 'nt':
                max_workers = 1
            else:
                max_workers = min(len(pages_to_ocr), os.cpu_count() or 1, 4)
            if max_workers > 1:
                with ProcessPoolExecutor(max_workers=max_workers, initializer=_init_ocr_worker) as executor:
                    # Submit all pages
                    futures = {
                        page_num: executor.submit(_ocr_page_task, str(pdf_path), page_num)
                        for page_num in pages_to_ocr
                    }
                    # Gather results
                    for page_num, future in futures.items():
                        try:
                            page_res = future.result()
                            page_text = "\n".join([l["text"] for l in page_res["lines"]])
                            results[f"page_{page_num}"] = page_text
                        except Exception as e:
                            results[f"page_{page_num}"] = f"[OCR Error on page {page_num}: {e}]"
            else:
                # Sequential fallback if only 1 page to OCR or single core CPU
                for page_num in pages_to_ocr:
                    try:
                        page_res = _ocr_page_task(str(pdf_path), page_num)
                        page_text = "\n".join([l["text"] for l in page_res["lines"]])
                        results[f"page_{page_num}"] = page_text
                    except Exception as e:
                        results[f"page_{page_num}"] = f"[OCR Error on page {page_num}: {e}]"

        return results

    def extract_page_results(self, file_path: Path) -> list[dict[str, Any]]:
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        
        if suffix == ".pdf":
            doc = fitz.open(str(file_path))
            pages_to_ocr = list(range(1, len(doc) + 1))
            results = []
                    
            if pages_to_ocr:
                from concurrent.futures import ProcessPoolExecutor
                # On Windows, ProcessPoolExecutor with PaddlePaddle/PaddleOCR is prone to deadlocks/hangs.
                if os.name == 'nt':
                    max_workers = 1
                else:
                    max_workers = min(len(pages_to_ocr), os.cpu_count() or 1, 4)
                ocr_results = {}
                if max_workers > 1:
                    with ProcessPoolExecutor(max_workers=max_workers, initializer=_init_ocr_worker) as executor:
                        futures = {
                            page_num: executor.submit(_ocr_page_task, str(file_path), page_num)
                            for page_num in pages_to_ocr
                        }
                        for page_num, future in futures.items():
                            ocr_results[page_num] = future.result()
                else:
                    for page_num in pages_to_ocr:
                        ocr_results[page_num] = _ocr_page_task(str(file_path), page_num)
                        
                for page_num in pages_to_ocr:
                    results.append(ocr_results[page_num])
                    
            # Sort by page number
            results.sort(key=lambda x: x["page_number"])
            return results
            
        elif suffix in {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}:
            ocr_result = self.ocr_client.ocr(str(file_path))
            lines = _parse_ocr_result(ocr_result)
            # Read image for re-OCR crop processing
            img = cv2.imread(str(file_path))
            if img is not None:
                lines = _re_ocr_low_confidence_lines(img, lines, self.ocr_client)
            avg_conf = np.mean([l["confidence"] for l in lines]) if lines else 0.0
            
            img_pil = Image.open(file_path)
            width, height = img_pil.size
            
            return [{
                "page_number": 1,
                "lines": lines,
                "width": width,
                "height": height,
                "confidence": float(avg_conf)
            }]
            
        elif suffix == ".docx":
            from .documents import _read_docx_bytes
            text = _read_docx_bytes(file_path.read_bytes())
            ocr_lines = [{"text": line.strip(), "box": [], "confidence": 1.0} for line in text.splitlines() if line.strip()]
            return [{
                "page_number": 1,
                "lines": ocr_lines,
                "width": 0,
                "height": 0,
                "confidence": 1.0
            }]
            
        # Fallback text
        text = file_path.read_text("utf-8", errors="ignore")
        ocr_lines = [{"text": line.strip(), "box": [], "confidence": 1.0} for line in text.splitlines() if line.strip()]
        return [{
            "page_number": 1,
            "lines": ocr_lines,
            "width": 0,
            "height": 0,
            "confidence": 1.0
        }]

    def extract_from_file(self, file_path: Path) -> str:
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            page_map = self.extract_text_from_pdf(file_path)
            return "\n\n".join(page_map.values())
        elif suffix in {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}:
            # For pure images, run PaddleOCR directly
            ocr_result = self.ocr_client.ocr(str(file_path))
            ocr_lines = []
            if ocr_result and ocr_result[0]:
                if isinstance(ocr_result[0], dict):
                    # PaddleOCR 3.x dict format
                    ocr_lines.extend(ocr_result[0].get("rec_texts", []))
                else:
                    # Classic PaddleOCR nested list format
                    for line in ocr_result[0]:
                        if line and len(line) > 1 and line[1]:
                            ocr_lines.append(str(line[1][0]))
            return "\n".join(ocr_lines)
        elif suffix == ".docx":
            # Direct word zip extraction
            from .documents import _read_docx_bytes
            return _read_docx_bytes(file_path.read_bytes())
        
        # Fallback text read
        return file_path.read_text("utf-8", errors="ignore")

    def extract_from_upload(self, upload: UploadFile, subfolder: str = "documents") -> tuple[Path, str]:
        saved_path = save_upload(upload, subfolder)
        return saved_path, self.extract_from_file(saved_path)

    def extract_bundle(self, uploads: list[UploadFile]) -> dict[str, dict[str, Any]]:
        bundle: dict[str, dict[str, Any]] = {}
        for upload in uploads:
            saved_path, extracted_text = self.extract_from_upload(upload)
            source_name = Path(upload.filename or saved_path.name).stem.upper()
            bundle[source_name] = {
                "file_name": upload.filename or saved_path.name,
                "file_path": str(saved_path),
                "text": extracted_text,
            }
        return bundle