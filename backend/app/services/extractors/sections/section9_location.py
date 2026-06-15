from typing import Any
import re
from app.services.extractors.base import extract_field_by_labels, create_scored_field

def extract_section9(text: str) -> dict[str, Any]:
    """
    Extracts Location fields.
    """
    try:
        # Plot Number
        plot_labels = ["Plot Number", "Plot No.", "Plot No", "PlotNo.", "PlotNo"]
        plot_res = extract_field_by_labels(text, plot_labels, "plot_number")

        # Survey Number
        survey_labels = [
            "Survey Number", "Survey No.", "Survey No", "SurveyNo", "Sy No.", "Sy No", "SyNo", "SURVEY NO", "Survey No./Gramkhantam/Abadi"
        ]
        survey_res = extract_field_by_labels(text, survey_labels, "survey_number")
        if not survey_res.get("value"):
            fallback_val = _extract_survey_fallback(text)
            if fallback_val:
                survey_res = create_scored_field(fallback_val, regex_confidence=0.60, final_confidence=0.60)

        # Door Number
        door_labels = ["Door Number", "Door No.", "Door No", "D.No.", "D No.", "D No", "H.No.", "House No", "Flat No", "Flat Number"]
        door_res = extract_field_by_labels(text, door_labels, "door_number")

        # TS Number
        ts_labels = ["TS Number", "TS No.", "TS No", "T.S.No.", "T.S. No", "Town Survey Number", "Town Survey No"]
        ts_res = extract_field_by_labels(text, ts_labels, "ts_number")

        # Village
        village_labels = ["Village", "Village Name", "Mouza"]
        village_res = extract_field_by_labels(text, village_labels, "village")

        # Ward
        ward_labels = ["Ward", "Ward No", "Ward Number"]
        ward_res = extract_field_by_labels(text, ward_labels, "ward")

        # Taluka
        taluka_labels = ["Taluka", "Tehsil", "Tahsil"]
        taluka_res = extract_field_by_labels(text, taluka_labels, "taluka")

        # Mandal
        mandal_labels = ["Mandal", "Mandal Name"]
        mandal_res = extract_field_by_labels(text, mandal_labels, "mandal")

        # District
        district_labels = ["District", "Dist."]
        district_res = extract_field_by_labels(text, district_labels, "district")

        # Layout Approval Date
        layout_approval_date_labels = ["Layout Approval Date", "Layout Date"]
        layout_approval_date_res = extract_field_by_labels(text, layout_approval_date_labels, "layout_approval_date")

        # Layout Approval Validity
        layout_approval_validity_labels = ["Layout Approval Validity", "Validity Date"]
        layout_approval_validity_res = extract_field_by_labels(text, layout_approval_validity_labels, "layout_approval_validity")

        # Approved Plan Authority
        approved_plan_authority_labels = ["Approved Plan Authority", "Sanctioning Authority", "Authority"]
        approved_plan_authority_res = extract_field_by_labels(text, approved_plan_authority_labels, "approved_plan_authority")

        # Approved Plan Verified
        approved_plan_verified_labels = ["Approved Plan Verified", "Plan Verified"]
        approved_plan_verified_res = extract_field_by_labels(text, approved_plan_verified_labels, "approved_plan_verified")

        # Approved Plan Comments
        approved_plan_comments_labels = ["Approved Plan Comments", "Comments"]
        approved_plan_comments_res = extract_field_by_labels(text, approved_plan_comments_labels, "approved_plan_comments")

        return {
            "plot_number": plot_res,
            "survey_number": survey_res,
            "door_number": door_res,
            "ts_number": ts_res,
            "village": village_res,
            "ward": ward_res,
            "taluka": taluka_res,
            "mandal": mandal_res,
            "district": district_res,
            "layout_approval_date": layout_approval_date_res,
            "layout_approval_validity": layout_approval_validity_res,
            "approved_plan_authority": approved_plan_authority_res,
            "approved_plan_verified": approved_plan_verified_res,
            "approved_plan_comments": approved_plan_comments_res
        }
    except Exception:
        return {
            "plot_number": create_scored_field(None),
            "survey_number": create_scored_field(None),
            "door_number": create_scored_field(None),
            "ts_number": create_scored_field(None),
            "village": create_scored_field(None),
            "ward": create_scored_field(None),
            "taluka": create_scored_field(None),
            "mandal": create_scored_field(None),
            "district": create_scored_field(None),
            "layout_approval_date": create_scored_field(None),
            "layout_approval_validity": create_scored_field(None),
            "approved_plan_authority": create_scored_field(None),
            "approved_plan_verified": create_scored_field(None),
            "approved_plan_comments": create_scored_field(None)
        }

def _extract_survey_fallback(text: str) -> str | None:
    net_plot_match = re.search(r"Net Plot Area[^\n]+?(\d+/[A-Z0-9/,-]+(?:\s*,\s*\d+/[A-Z0-9/,-]+)*)", text, flags=re.IGNORECASE)
    if net_plot_match:
        return re.sub(r"\s+", " ", net_plot_match.group(1)).strip()
    
    MONTH_ABBRS = {"jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"}
    
    matches = re.findall(r"\b\d{2,4}/[A-Z0-9/,-]+\b", text, flags=re.IGNORECASE)
    if matches:
        for m in matches:
            m_clean = m.strip().lower()
            if re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", m_clean):
                continue
            if re.search(r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b", m_clean):
                continue
            is_abbr = False
            for abbr in MONTH_ABBRS:
                if m_clean.startswith(abbr):
                    is_abbr = True
                    break
            if not is_abbr:
                return re.sub(r"\s+", " ", m).strip()
    return None
