"""
PDF report generator for election predictions.
"""
import io
import base64
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def generate_pdf_report(prediction_data: dict) -> bytes:
    if not HAS_REPORTLAB:
        raise RuntimeError("reportlab is not installed.")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"],
                                 fontSize=20, textColor=colors.HexColor("#6366f1"),
                                 spaceAfter=6)
    heading_style = ParagraphStyle("heading", parent=styles["Heading2"],
                                   fontSize=13, textColor=colors.HexColor("#818cf8"),
                                   spaceBefore=14, spaceAfter=6)
    normal_style = ParagraphStyle("normal", parent=styles["Normal"],
                                  fontSize=10, textColor=colors.HexColor("#374151"))

    story = []

    # Title
    story.append(Paragraph("🗳  Election Outcome Prediction Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        normal_style
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=colors.HexColor("#6366f1"), spaceAfter=12))

    # Candidate Info
    story.append(Paragraph("Candidate Information", heading_style))
    cand_data = [
        ["Field", "Value"],
        ["Candidate Name", prediction_data.get("candidate_name", "N/A")],
        ["Popularity Score", str(prediction_data.get("popularity_score", "N/A"))],
        ["Campaign Spending ($)", str(prediction_data.get("campaign_spending", "N/A"))],
        ["Social Media Score", str(prediction_data.get("social_media_score", "N/A"))],
        ["Department", str(prediction_data.get("department", "N/A"))],
        ["Past Performance", str(prediction_data.get("past_performance", "N/A"))],
        ["Engagement Level", str(prediction_data.get("engagement_level", "N/A"))],
    ]
    t = Table(cand_data, colWidths=[7*cm, 10*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f9fafb"), colors.HexColor("#f3f4f6")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    # Prediction Results
    story.append(Paragraph("Prediction Results", heading_style))
    cart_result = prediction_data.get("cart_prediction", "N/A")
    cart_conf   = prediction_data.get("cart_confidence", "N/A")
    rf_result   = prediction_data.get("rf_prediction", "N/A")
    rf_conf     = prediction_data.get("rf_confidence", "N/A")

    pred_data = [
        ["Model", "Prediction", "Confidence"],
        ["CART (Decision Tree)", cart_result, f"{cart_conf}%"],
        ["Random Forest", rf_result, f"{rf_conf}%"],
    ]
    t2 = Table(pred_data, colWidths=[7*cm, 5*cm, 5*cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f0fdf4"), colors.HexColor("#f9fafb")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
    ]))
    story.append(t2)

    # Top Factors
    factors = prediction_data.get("top_influencing_factors", [])
    if factors:
        story.append(Paragraph("Top Influencing Factors", heading_style))
        factor_rows = [["Rank", "Feature", "Importance Score"]]
        for i, f in enumerate(factors, 1):
            factor_rows.append([str(i), f["feature"].replace("_", " ").title(),
                                 f"{f['importance']:.4f}"])
        t3 = Table(factor_rows, colWidths=[2*cm, 9*cm, 6*cm])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#f9fafb"), colors.HexColor("#f3f4f6")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(t3)

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#9ca3af")))
    story.append(Paragraph(
        "CART-Based Student Government Election Outcome Prediction System | Auto-generated Report",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=1)
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()
