"""HAM10000 seven-class lesion taxonomy and demo risk mapping.

Base risk levels are a simplified illustrative mapping (malignant/precancerous
classes -> high, benign-but-worth-checking -> medium, common benign -> low),
not a clinically validated triage rule.
"""
from __future__ import annotations

CLASS_ORDER = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]

CLASS_INFO = {
    "akiec": {
        "label_ko": "광선각화증/보웬병 의심",
        "label_en": "Actinic keratosis / intraepithelial carcinoma",
        "base_risk": "high",
    },
    "bcc": {
        "label_ko": "기저세포암 의심",
        "label_en": "Basal cell carcinoma",
        "base_risk": "high",
    },
    "bkl": {
        "label_ko": "양성 각화증",
        "label_en": "Benign keratosis-like lesion",
        "base_risk": "medium",
    },
    "df": {
        "label_ko": "피부섬유종",
        "label_en": "Dermatofibroma",
        "base_risk": "low",
    },
    "mel": {
        "label_ko": "흑색종 의심",
        "label_en": "Melanoma",
        "base_risk": "high",
    },
    "nv": {
        "label_ko": "일반 점(모반)",
        "label_en": "Melanocytic nevus",
        "base_risk": "low",
    },
    "vasc": {
        "label_ko": "혈관 병변",
        "label_en": "Vascular lesion",
        "base_risk": "low",
    },
}

LOW_CONFIDENCE_THRESHOLD = 0.5
RISK_UPGRADE = {"low": "medium", "medium": "high", "high": "high"}

GUIDANCE_KO = {
    "high": (
        "고위험 소견입니다. 정확한 진단을 위해 가능한 빨리 피부과 전문의의 진료를 받으시길 권장합니다."
    ),
    "medium": (
        "경과 관찰이 필요한 소견입니다. 병변의 크기, 색, 모양에 변화가 있는지 주기적으로 확인하고 "
        "피부과 방문을 고려해보세요."
    ),
    "low": (
        "특별한 위험 소견은 보이지 않습니다. 다만 병변의 크기, 색, 모양에 변화가 생기면 "
        "피부과 상담을 받으시길 권장합니다."
    ),
}


def compute_risk(predicted_class: str, confidence: float) -> tuple[str, bool]:
    """Return (risk_level, was_upgraded_for_low_confidence)."""
    base_risk = CLASS_INFO[predicted_class]["base_risk"]
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        return RISK_UPGRADE[base_risk], True
    return base_risk, False
