import io

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.classes import CLASS_INFO, GUIDANCE_KO, compute_risk
from app.predictor import get_predictor
from app.quality import check_image_quality
from app.schemas import AnalyzeResponse

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


async def load_upload_image(file: UploadFile) -> Image.Image:
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="이미지 파일이 너무 큽니다 (최대 10MB).")
    try:
        return Image.open(io.BytesIO(data))
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="이미지 파일을 열 수 없습니다. 다른 파일을 시도해주세요.")


def run_analysis(image: Image.Image) -> AnalyzeResponse:
    quality_warnings = check_image_quality(image)

    probabilities = get_predictor().predict(image)
    predicted_class = max(probabilities, key=probabilities.get)
    confidence = probabilities[predicted_class]

    risk_level, was_upgraded = compute_risk(predicted_class, confidence)
    info = CLASS_INFO[predicted_class]

    return AnalyzeResponse(
        predicted_class=predicted_class,
        label_ko=info["label_ko"],
        label_en=info["label_en"],
        confidence=confidence,
        probabilities=probabilities,
        risk_level=risk_level,
        risk_upgraded_low_confidence=was_upgraded,
        guidance=GUIDANCE_KO[risk_level],
        quality_warnings=quality_warnings,
    )
