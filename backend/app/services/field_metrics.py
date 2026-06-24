import json
from pathlib import Path
from typing import Any

METRICS_FILE = Path(__file__).resolve().parent.parent.parent / "storage" / "field_metrics.json"

def init_metrics() -> dict[str, Any]:
    if METRICS_FILE.exists():
        try:
            return json.loads(METRICS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_metrics(metrics: dict[str, Any]) -> None:
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    METRICS_FILE.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

def record_field_extraction(field_code: str, success: bool, confidence: float, validation_error: bool) -> None:
    metrics = init_metrics()
    if field_code not in metrics:
        metrics[field_code] = {
            "total_attempts": 0,
            "successes": 0,
            "failures": 0,
            "validation_errors": 0,
            "average_confidence": 0.0
        }
    
    m = metrics[field_code]
    m["total_attempts"] += 1
    if success:
        m["successes"] += 1
    else:
        m["failures"] += 1
        
    if validation_error:
        m["validation_errors"] += 1
        
    # Recalculate average confidence
    total = m["total_attempts"]
    m["average_confidence"] = ((m["average_confidence"] * (total - 1)) + confidence) / total
    save_metrics(metrics)

def get_field_metrics() -> dict[str, Any]:
    return init_metrics()
