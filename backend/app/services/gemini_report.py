"""Generates a plain-language explanation of a lesion classification using Gemini.

Requires the GEMINI_API_KEY env var (get one at https://aistudio.google.com/apikey).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from fastapi import HTTPException
from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel

from app.schemas.gemini_report import ClassPrediction

MODEL_NAME = "gemini-3.5-flash"

# HAM10000 classes that are malignant or pre-malignant -> always urge a prompt dermatologist
# visit instead of self-care tips. Kept in sync with the risk tiers in frontend/js/results.js.
HIGH_RISK_IDS = {"mel", "akiec", "bcc"}

HIGH_RISK_INSTRUCTION = (
    "This falls into a higher-risk category (malignant or pre-malignant). Clearly and firmly "
    "recommend seeing a dermatologist as soon as possible -- do not suggest self-care as a "
    "substitute. Briefly explain, in plain language, why prompt medical evaluation matters for "
    "this specific condition."
)
SELF_CARE_INSTRUCTION = (
    "This falls into a lower-risk category. Provide 2-3 concrete, practical self-care tips "
    "specific to this condition (e.g. sun protection, avoiding irritation, what to keep an eye "
    "on). Also mention briefly what changes (size, color, shape, bleeding, itching) should "
    "prompt a doctor visit even though routine care is otherwise fine."
)

PROMPT_TEMPLATE = """You are an AI assistant supporting dermatology care. The attached image is a photo
a patient took of a skin lesion. An AI classification model's top prediction for this lesion is:

{disease_name}

Do not mention or imply any confidence score, probability, or percentage anywhere in your answer --
just refer to this as the predicted condition. Look at the image directly and write the following
three items:

1. report: written in English, organized as follows:
   - Briefly explain in plain language what "{disease_name}" generally is and what typically
     causes it (2-3 sentences).
   - {guidance_instruction}
   - The final sentence must state that this is a reference-only AI analysis, not a medical
     diagnosis.
2. texture_note: one sentence on the lesion's border/texture as actually observed in the image
   (e.g. whether the border is smooth or irregular, whether it's asymmetric). Describe only what
   is actually visible in the image.
3. pigment_note: one sentence on the lesion's color/pigment distribution as actually observed in
   the image (e.g. a single uniform tone vs. multiple colors mixed together). Describe only what
   is actually visible in the image.

Write all three items in English.
"""


class GeminiAnalysis(BaseModel):
    report: str
    texture_note: str
    pigment_note: str


@dataclass
class ReportResult:
    report: str
    texture_note: str
    pigment_note: str


@lru_cache
def _get_client() -> genai.Client:
    return genai.Client()


def generate_report(predictions: list[ClassPrediction], image: Image.Image) -> ReportResult:
    top = max(predictions, key=lambda p: p.probability)
    guidance_instruction = HIGH_RISK_INSTRUCTION if top.id in HIGH_RISK_IDS else SELF_CARE_INSTRUCTION
    prompt = PROMPT_TEMPLATE.format(disease_name=top.name, guidance_instruction=guidance_instruction)

    try:
        response = _get_client().models.generate_content(
            model=MODEL_NAME,
            contents=[image, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeminiAnalysis,
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini report generation failed: {exc}") from exc

    analysis: GeminiAnalysis = response.parsed
    return ReportResult(
        report=analysis.report,
        texture_note=analysis.texture_note,
        pigment_note=analysis.pigment_note,
    )
