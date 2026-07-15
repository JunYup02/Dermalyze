from fastapi import APIRouter, File, UploadFile

from app.analysis import load_upload_image, run_analysis
from app.schemas import AnalyzeResponse

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(file: UploadFile = File(...)):
    image = await load_upload_image(file)
    return run_analysis(image)
