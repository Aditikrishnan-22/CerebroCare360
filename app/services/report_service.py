import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from flask import current_app

def generate_report(scan, prediction, user):
    """
    Generates a PDF report for a given scan and prediction.
    Returns the file path of the saved PDF.
    """
    # Create folder per user
    reports_dir = os.path.join(current_app.root_path, 'static', 'reports', str(user.id))
    os.makedirs(reports_dir, exist_ok=True)

    filename = f"report_{scan.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join(reports_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # ── Colours ──────────────────────────────────────────────
    PRIMARY     = colors.HexColor('#3b4fd8')
    ACCENT      = colors.HexColor('#7c3aed')
    LIGHT_BG    = colors.HexColor('#eef0fd')
    DANGER      = colors.HexColor('#dc2626')
    SUCCESS     = colors.HexColor('#059669')
    TEXT_MUTED  = colors.HexColor('#9199b0')
    BORDER      = colors.HexColor('#e4e7f0')
    WHITE       = colors.white
    DARK        = colors.HexColor('#0f1525')

    # ── Styles ───────────────────────────────────────────────
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title', fontSize=24, textColor=WHITE,
        fontName='Helvetica-Bold', alignment=TA_CENTER, spaceAfter=8, leading=30
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', fontSize=12, textColor=colors.HexColor('#c7d2fe'),
        fontName='Helvetica', alignment=TA_CENTER, leading=16
    )
    section_style = ParagraphStyle(
        'Section', fontSize=12, textColor=PRIMARY,
        fontName='Helvetica-Bold', spaceBefore=16, spaceAfter=8
    )
    body_style = ParagraphStyle(
        'Body', fontSize=10, textColor=DARK,
        fontName='Helvetica', spaceAfter=4, leading=16
    )
    muted_style = ParagraphStyle(
        'Muted', fontSize=9, textColor=TEXT_MUTED,
        fontName='Helvetica', spaceAfter=4
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer', fontSize=9, textColor=colors.HexColor('#92400e'),
        fontName='Helvetica', leading=14, alignment=TA_LEFT
    )

    story = []

    # ── Header banner ─────────────────────────────────────────
    header_data = [
        [Paragraph('CerebroCare360', title_style)],
        [Paragraph('AI-Assisted Brain Tumor Detection Report', subtitle_style)]
    ]

    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), PRIMARY),
        ('TOPPADDING',    (0,0), (-1,0), 24),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING',    (0,1), (-1,1), 2),
        ('BOTTOMPADDING', (0,1), (-1,1), 24),
        ('LEFTPADDING',   (0,0), (-1,-1), 12),
        ('RIGHTPADDING',  (0,0), (-1,-1), 12),
        ('ROUNDEDCORNERS', [10]),
    ]))

    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Patient info ──────────────────────────────────────────
    story.append(Paragraph('Patient Information', section_style))

    patient_data = [
        ['Patient Name',  user.full_name,      'Report Date', datetime.utcnow().strftime('%d %B %Y')],
        ['Email',         user.email,           'Scan ID',     f'#{scan.id}'],
        ['Scan Date',     scan.upload_date.strftime('%d %B %Y, %H:%M'), 'Model Version', prediction.model_version],
    ]

    patient_table = Table(patient_data, colWidths=[4*cm, 5.5*cm, 3.5*cm, 4*cm])
    patient_table.setStyle(TableStyle([
        ('FONTNAME',     (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME',     (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',     (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,-1), 9),
        ('TEXTCOLOR',    (0,0), (0,-1), TEXT_MUTED),
        ('TEXTCOLOR',    (2,0), (2,-1), TEXT_MUTED),
        ('TEXTCOLOR',    (1,0), (1,-1), DARK),
        ('TEXTCOLOR',    (3,0), (3,-1), DARK),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [LIGHT_BG, WHITE]),
        ('TOPPADDING',   (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0), (-1,-1), 8),
        ('LEFTPADDING',  (0,0), (-1,-1), 10),
        ('GRID',         (0,0), (-1,-1), 0.5, BORDER),
        ('ROUNDEDCORNERS', [4]),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.3*cm))

    # ── Result ────────────────────────────────────────────────
    story.append(Paragraph('Analysis Result', section_style))

    if prediction.has_tumor:
        result_text  = f'TUMOR DETECTED — {prediction.tumor_type.upper()}'
        result_color = DANGER
        result_bg    = colors.HexColor('#fef2f2')
    else:
        result_text  = 'NO TUMOR DETECTED'
        result_color = SUCCESS
        result_bg    = colors.HexColor('#ecfdf5')

    verdict_style = ParagraphStyle(
        'Verdict', fontSize=16, textColor=result_color,
        fontName='Helvetica-Bold', alignment=TA_CENTER
    )
    conf_style = ParagraphStyle(
        'Conf', fontSize=10, textColor=result_color,
        fontName='Helvetica', alignment=TA_CENTER
    )

    verdict_data = [[
        Paragraph(result_text, verdict_style),
    ],[
        Paragraph(f'Confidence: {prediction.confidence * 100:.1f}%', conf_style),
    ]]

    verdict_table = Table(verdict_data, colWidths=[17*cm])
    verdict_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), result_bg),
        ('TOPPADDING',    (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('LEFTPADDING',   (0,0), (-1,-1), 12),
        ('RIGHTPADDING',  (0,0), (-1,-1), 12),
        ('BOX',           (0,0), (-1,-1), 1.5, result_color),
        ('ROUNDEDCORNERS', [8]),
    ]))
    story.append(verdict_table)
    story.append(Spacer(1, 0.3*cm))

    # ── GradCAM Heatmap ───────────────────────────────────────
    if prediction.heatmap_filename:
        heatmap_path = os.path.join(current_app.root_path, 'static', 'heatmaps', prediction.heatmap_filename)
        if os.path.exists(heatmap_path):
            story.append(Paragraph('GradCAM Analysis', section_style))
            story.append(Paragraph("This highlights the regions of the MRI that contributed most to the AI model's prediction. Red/yellow areas indicate higher importance.", body_style))
            story.append(Spacer(1, 0.2*cm))
            story.append(RLImage(heatmap_path, width=8*cm, height=8*cm))
            story.append(Spacer(1, 0.5*cm))

    # ── Probability breakdown ─────────────────────────────────
    story.append(Paragraph('Probability Breakdown', section_style))

    prob_data = [
        ['Class', 'Probability', 'Confidence Bar'],
        ['Glioma',      f'{prediction.prob_glioma * 100:.1f}%',      ''],
        ['Meningioma',  f'{prediction.prob_meningioma * 100:.1f}%',   ''],
        ['No Tumor',    f'{prediction.prob_notumor * 100:.1f}%',      ''],
        ['Pituitary',   f'{prediction.prob_pituitary * 100:.1f}%',    ''],
    ]

    prob_table = Table(prob_data, colWidths=[5*cm, 4*cm, 8*cm])
    prob_table.setStyle(TableStyle([
        ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
        ('BACKGROUND',    (0,0), (-1,0),  PRIMARY),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [LIGHT_BG, WHITE]),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('GRID',          (0,0), (-1,-1), 0.5, BORDER),
        ('ALIGN',         (1,0), (1,-1),  'CENTER'),
        ('TEXTCOLOR',     (1,1), (1,-1),  PRIMARY),
        ('FONTNAME',      (1,1), (1,-1),  'Helvetica-Bold'),
    ]))
    story.append(prob_table)
    story.append(Spacer(1, 0.3*cm))

    # ── Model info ────────────────────────────────────────────
    story.append(Paragraph('Model Information', section_style))
    story.append(Paragraph(
        'This analysis was performed using a weighted ensemble of three deep learning models: '
        '<b>VGG16</b>, <b>ResNet50</b>, and <b>EfficientNetB0</b>. '
        'Each model was trained on the Masoud Nickparvar brain tumor MRI dataset '
        'containing 4 classes: Glioma, Meningioma, No Tumor, and Pituitary.',
        body_style
    ))
    story.append(Spacer(1, 0.2*cm))

    # ── Disclaimer ────────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=1, color=BORDER))
    story.append(Spacer(1, 0.2*cm))

    disclaimer_data = [[
        Paragraph(
            '<b>⚠ Medical Disclaimer:</b> This report is generated by an AI system for '
            'educational and informational purposes only. It does not constitute a medical '
            'diagnosis and should not be used as a substitute for professional medical advice, '
            'diagnosis, or treatment. Always consult a qualified neurologist or medical '
            'professional regarding any medical condition. CerebroCare360 accepts no '
            'liability for decisions made based on this report.',
            disclaimer_style
        )
    ]]
    disclaimer_table = Table(disclaimer_data, colWidths=[17*cm])
    disclaimer_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), colors.HexColor('#fffbeb')),
        ('TOPPADDING',    (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING',   (0,0), (-1,-1), 12),
        ('RIGHTPADDING',  (0,0), (-1,-1), 12),
        ('BOX',           (0,0), (-1,-1), 1, colors.HexColor('#fde68a')),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(disclaimer_table)

    # ── Footer ────────────────────────────────────────────────
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f'Generated by CerebroCare360 &nbsp;·&nbsp; {datetime.utcnow().strftime("%d %B %Y at %H:%M UTC")}',
        muted_style
    ))

    doc.build(story)

    return f'reports/{user.id}/{filename}'