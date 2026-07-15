from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response

from app.analysis import load_upload_image, run_analysis
from app.pdf import build_pdf

router = APIRouter()


@router.post("/report")
async def report(file: UploadFile = File(...)):
    image = await load_upload_image(file)
    result = run_analysis(image)
    pdf_bytes = build_pdf(image, result)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=skin-analysis-report.pdf"},
    )
