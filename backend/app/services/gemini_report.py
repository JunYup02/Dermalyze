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

MODEL_NAME = "gemini-2.5-flash"

PROMPT_TEMPLATE = """당신은 피부과 진료를 보조하는 AI 어시스턴트입니다. 첨부된 이미지는 환자가 촬영한 피부
병변 사진이고, 아래는 그 이미지를 AI 분류 모델로 분석한 결과이며 확률이 높은 순서대로 나열되어 있습니다.

{predictions}

이미지를 직접 보고 다음 세 가지를 각각 작성하세요:

1. report: 3~5문장의 한국어. 가장 가능성 높은 병명을 쉬운 말로 설명하고, 그 확률이 다른 후보들과 비교했을 때
   얼마나 확실한 수준인지 언급하고, 권장 다음 행동(병원 방문 필요 여부 등)을 제시하세요. 마지막 문장에는 이것이
   의학적 진단이 아니라 참고용 AI 분석이라는 점을 반드시 명시하세요.
2. texture_note: 이미지에서 실제로 관찰되는 병변의 경계·질감에 대한 한 문장 (예: 경계가 매끄러운지 불규칙한지,
   비대칭 여부). 이미지에 실제로 보이는 내용만 서술하세요.
3. pigment_note: 이미지에서 실제로 관찰되는 병변의 색상·색소 분포에 대한 한 문장 (예: 단일 색조인지 여러 색이
   섞여 있는지). 이미지에 실제로 보이는 내용만 서술하세요.
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
