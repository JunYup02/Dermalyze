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

# Set as both a system_instruction and repeated inline in the prompt itself --
# belt and suspenders against the model matching some other language cue (e.g.
# variable names, or just drifting) instead of the instruction.
SYSTEM_INSTRUCTION = (
    "You always respond in English only, regardless of what language anything else in the "
    "conversation or request is in. Never output Korean or any language other than English."
)

PROMPT_TEMPLATE = """You are an AI assistant supporting a dermatology workflow. The attached image is a
photo of a skin lesion taken by the patient. Below is the output of an AI classification model that
analyzed the image, listed in descending order of probability.

{predictions}

Look at the image yourself and write the following three fields. IMPORTANT: every field must be written
in English only -- do not use Korean or any other language, even if it feels more natural for the
content.

1. report: 3-5 sentences in English. Explain the most likely diagnosis in plain language, note how
   confident that probability is compared to the other candidates, and suggest a recommended next step
   (e.g. whether an in-person visit is warranted). The final sentence must state that this is a
   reference-only AI analysis, not a medical diagnosis.
2. texture_note: One sentence in English on the lesion's border/texture as actually observed in the
   image (e.g. whether the border is smooth or irregular, symmetric or not). Describe only what is
   actually visible in the image.
3. pigment_note: One sentence in English on the lesion's color/pigment distribution as actually
   observed in the image (e.g. a single tone vs. multiple colors mixed together). Describe only what is
   actually visible in the image.

Reminder: report, texture_note, and pigment_note must all be in English.
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
    predictions_text = "\n".join(
        f"{i + 1}. {p.name} ({p.probability:.1%})" for i, p in enumerate(predictions)
    )
    prompt = PROMPT_TEMPLATE.format(predictions=predictions_text)

    try:
        response = _get_client().models.generate_content(
            model=MODEL_NAME,
            contents=[image, prompt],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
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
