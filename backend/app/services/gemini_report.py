"""Generates a plain-language explanation of a lesion classification using Gemini.

Requires the GEMINI_API_KEY env var (get one at https://aistudio.google.com/apikey).
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import HTTPException
from google import genai

from app.schemas.gemini_report import ClassPrediction

MODEL_NAME = "gemini-3.5-flash"

PROMPT_TEMPLATE = """당신은 피부과 진료를 보조하는 AI 어시스턴트입니다. 아래는 피부 병변 이미지를 AI 모델로
분류한 결과이며, 확률이 높은 순서대로 나열되어 있습니다.

{predictions}

다음 내용을 포함해서 3~5문장의 한국어로 작성하세요:
- 가장 가능성 높은 병명이 무엇인지 쉬운 말로 설명
- 그 확률이 다른 후보들과 비교했을 때 얼마나 확실한 수준인지
- 병명의 특성을 고려한 권장 다음 행동 (병원 방문 필요 여부 등)

마지막 문장에는 이것이 의학적 진단이 아니라 참고용 AI 분석이라는 점을 반드시 명시하세요.
"""


@lru_cache
def _get_client() -> genai.Client:
    return genai.Client()


def generate_report(predictions: list[ClassPrediction]) -> str:
    predictions_text = "\n".join(
        f"{i + 1}. {p.name} ({p.probability:.1%})" for i, p in enumerate(predictions)
    )
    prompt = PROMPT_TEMPLATE.format(predictions=predictions_text)

    try:
        response = _get_client().models.generate_content(model=MODEL_NAME, contents=prompt)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini report generation failed: {exc}") from exc

    return response.text
