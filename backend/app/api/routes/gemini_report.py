from fastapi import APIRouter, File, UploadFile

from app.schemas.gemini_report import GeminiReportResponse
from app.services.gemini_report import generate_report
from app.services.image import load_upload_image
from app.services.vertex_predictor import classify

router = APIRouter()


@router.post("/gemini-report", response_model=GeminiReportResponse)
async def create_gemini_report(file: UploadFile = File(...)):
    image = await load_upload_image(file)
    predictions = classify(image)
    report = generate_report(predictions)
    return GeminiReportResponse(predictions=predictions, report=report)
