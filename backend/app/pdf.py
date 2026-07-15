import io

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.classes import CLASS_INFO
from app.schemas import AnalyzeResponse

RISK_LABEL_KO = {"high": "고위험", "medium": "중위험", "low": "저위험"}

DISCLAIMER = (
    "본 리포트는 데모용 AI 모델이 생성한 참고 자료이며, 실제 임상 데이터로 학습되지 않았습니다. "
    "의학적 진단을 대체할 수 없으니 반드시 피부과 전문의의 진료를 받으시기 바랍니다."
)


def build_pdf(image: Image.Image, result: AnalyzeResponse) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("피부 병변 AI 분석 리포트 (데모)", styles["Title"]))
    story.append(Spacer(1, 6 * mm))

    thumb = image.convert("RGB").copy()
    thumb.thumbnail((300, 300))
    thumb_buffer = io.BytesIO()
    thumb.save(thumb_buffer, format="PNG")
    thumb_buffer.seek(0)
    story.append(RLImage(thumb_buffer, width=80 * mm, height=80 * mm * thumb.height / thumb.width))
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph(f"<b>예측 결과:</b> {result.label_ko} ({result.label_en})", styles["Normal"]))
    story.append(Paragraph(f"<b>신뢰도:</b> {result.confidence * 100:.1f}%", styles["Normal"]))
    story.append(Paragraph(f"<b>위험도:</b> {RISK_LABEL_KO[result.risk_level]}", styles["Normal"]))
    story.append(Spacer(1, 4 * mm))

    prob_rows = [["병변 분류", "확률"]]
    for code, prob in sorted(result.probabilities.items(), key=lambda kv: -kv[1]):
        prob_rows.append([f"{CLASS_INFO[code]['label_ko']} ({code})", f"{prob * 100:.1f}%"])
    table = Table(prob_rows, colWidths=[110 * mm, 30 * mm])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(table)
    story.append(Spacer(1, 6 * mm))

    story.append(Paragraph("<b>권장 사항</b>", styles["Heading3"]))
    story.append(Paragraph(result.guidance, styles["Normal"]))
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph("<b>의료 면책 조항</b>", styles["Heading4"]))
    story.append(Paragraph(DISCLAIMER, styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
