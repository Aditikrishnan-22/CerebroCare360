import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
from flask import current_app


# ── Colour palette ────────────────────────────────────────────────
PRIMARY    = colors.HexColor('#3b4fd8')
ACCENT     = colors.HexColor('#7c3aed')
LIGHT_BG   = colors.HexColor('#eef0fd')
DANGER     = colors.HexColor('#dc2626')
SUCCESS    = colors.HexColor('#059669')
WARNING    = colors.HexColor('#d97706')
TEXT_MUTED = colors.HexColor('#9199b0')
BORDER     = colors.HexColor('#e4e7f0')
WHITE      = colors.white
DARK       = colors.HexColor('#0f1525')
SURFACE2   = colors.HexColor('#f7f8fc')


def _prob_bar(prob: float, bar_width: float = 200, bar_height: float = 12) -> Drawing:
    """Return a ReportLab Drawing of a filled probability bar."""
    d = Drawing(bar_width, bar_height)
    # Background track
    d.add(Rect(0, 0, bar_width, bar_height,
               fillColor=colors.HexColor('#e4e7f0'), strokeColor=None))
    # Filled portion
    fill_w = max(2, bar_width * prob)
    if prob >= 0.75:
        fill_col = SUCCESS
    elif prob >= 0.50:
        fill_col = PRIMARY
    elif prob >= 0.25:
        fill_col = WARNING
    else:
        fill_col = colors.HexColor('#cbd5e1')
    d.add(Rect(0, 0, fill_w, bar_height,
               fillColor=fill_col, strokeColor=None))
    return d


def generate_report(scan, prediction, user):
    """
    Generates a PDF report for a given scan and prediction.
    Returns the relative file path of the saved PDF (for DB storage).
    """
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

    # ── Styles ───────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'Title', fontSize=22, textColor=WHITE,
        fontName='Helvetica-Bold', alignment=TA_CENTER,
        spaceAfter=6, leading=28
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', fontSize=11, textColor=colors.HexColor('#c7d2fe'),
        fontName='Helvetica', alignment=TA_CENTER, leading=16
    )
    section_style = ParagraphStyle(
        'Section', fontSize=11, textColor=PRIMARY,
        fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=7,
        borderPad=0
    )
    body_style = ParagraphStyle(
        'Body', fontSize=9.5, textColor=DARK,
        fontName='Helvetica', spaceAfter=4, leading=15
    )
    muted_style = ParagraphStyle(
        'Muted', fontSize=8.5, textColor=TEXT_MUTED,
        fontName='Helvetica', spaceAfter=4, alignment=TA_CENTER
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer', fontSize=8.5, textColor=colors.HexColor('#92400e'),
        fontName='Helvetica', leading=13, alignment=TA_LEFT
    )
    caption_style = ParagraphStyle(
        'Caption', fontSize=8, textColor=TEXT_MUTED,
        fontName='Helvetica', alignment=TA_CENTER, spaceBefore=4
    )

    story = []

    # ══════════════════════════════════════════════════════════════
    # 1. HEADER BANNER
    # ══════════════════════════════════════════════════════════════
    header_data = [
        [Paragraph('CerebroCare360', title_style)],
        [Paragraph('AI-Assisted Brain Tumor Detection Report', subtitle_style)]
    ]
    header_table = Table(header_data, colWidths=[17*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), PRIMARY),
        ('TOPPADDING',    (0,0), (-1,0),  22),
        ('BOTTOMPADDING', (0,0), (-1,0),  4),
        ('TOPPADDING',    (0,1), (-1,1),  2),
        ('BOTTOMPADDING', (0,1), (-1,1),  22),
        ('LEFTPADDING',   (0,0), (-1,-1), 12),
        ('RIGHTPADDING',  (0,0), (-1,-1), 12),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.45*cm))

    # ══════════════════════════════════════════════════════════════
    # 2. PATIENT INFORMATION
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph('Patient Information', section_style))

    patient_data = [
        ['Patient Name',  user.full_name,
         'Report Date',   datetime.utcnow().strftime('%d %B %Y')],
        ['Email',         user.email,
         'Scan ID',       f'#{scan.id}'],
        ['Scan Date',     scan.upload_date.strftime('%d %B %Y, %H:%M'),
         'Model Version', prediction.model_version or 'ensemble-v1'],
    ]
    patient_table = Table(patient_data, colWidths=[3.8*cm, 5.8*cm, 3.4*cm, 4*cm])
    patient_table.setStyle(TableStyle([
        ('FONTNAME',      (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME',      (0,0), (0,-1),  'Helvetica-Bold'),
        ('FONTNAME',      (2,0), (2,-1),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('TEXTCOLOR',     (0,0), (0,-1),  TEXT_MUTED),
        ('TEXTCOLOR',     (2,0), (2,-1),  TEXT_MUTED),
        ('TEXTCOLOR',     (1,0), (1,-1),  DARK),
        ('TEXTCOLOR',     (3,0), (3,-1),  DARK),
        ('ROWBACKGROUNDS',(0,0), (-1,-1), [LIGHT_BG, WHITE]),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('GRID',          (0,0), (-1,-1), 0.5, BORDER),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.3*cm))

    # ══════════════════════════════════════════════════════════════
    # 3. ANALYSIS RESULT VERDICT
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph('Analysis Result', section_style))

    if prediction.has_tumor:
        result_text  = f'TUMOR DETECTED — {prediction.tumor_type.replace("_"," ").upper()}'
        result_color = DANGER
        result_bg    = colors.HexColor('#fef2f2')
        border_col   = DANGER
    else:
        result_text  = 'NO TUMOR DETECTED'
        result_color = SUCCESS
        result_bg    = colors.HexColor('#ecfdf5')
        border_col   = SUCCESS

    verdict_style = ParagraphStyle(
        'Verdict', fontSize=15, textColor=result_color,
        fontName='Helvetica-Bold', alignment=TA_CENTER
    )
    conf_style = ParagraphStyle(
        'Conf', fontSize=10, textColor=result_color,
        fontName='Helvetica', alignment=TA_CENTER
    )

    conf_pct = prediction.confidence * 100
    low_conf_note = ''
    if conf_pct < 50:
        low_conf_note = ' &nbsp;⚠ Low confidence — interpret with caution'

    verdict_data = [
        [Paragraph(result_text, verdict_style)],
        [Paragraph(f'Confidence: {conf_pct:.1f}%{low_conf_note}', conf_style)],
    ]
    verdict_table = Table(verdict_data, colWidths=[17*cm])
    verdict_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), result_bg),
        ('TOPPADDING',    (0,0), (-1,-1), 14),
        ('BOTTOMPADDING', (0,0), (-1,-1), 14),
        ('LEFTPADDING',   (0,0), (-1,-1), 12),
        ('RIGHTPADDING',  (0,0), (-1,-1), 12),
        ('BOX',           (0,0), (-1,-1), 1.5, border_col),
    ]))
    story.append(verdict_table)
    story.append(Spacer(1, 0.35*cm))

    # ══════════════════════════════════════════════════════════════
    # 4. MRI IMAGE + GRADCAM SIDE BY SIDE
    # ══════════════════════════════════════════════════════════════
    mri_path     = os.path.join(current_app.root_path, 'static', 'uploads', scan.image_filename)
    heatmap_path = None
    if prediction.heatmap_filename:
        _hp = os.path.join(current_app.root_path, 'static', 'heatmaps', prediction.heatmap_filename)
        if os.path.exists(_hp):
            heatmap_path = _hp

    IMG_W = 7.5*cm
    IMG_H = 7.5*cm

    if os.path.exists(mri_path):
        story.append(Paragraph('MRI Scan Analysis', section_style))

        if heatmap_path:
            # Side-by-side: Original | GradCAM
            img_row = [[
                RLImage(mri_path,     width=IMG_W, height=IMG_H),
                RLImage(heatmap_path, width=IMG_W, height=IMG_H),
            ]]
            img_table = Table(img_row, colWidths=[8.5*cm, 8.5*cm])
            img_table.setStyle(TableStyle([
                ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
                ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING',    (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING',   (0,0), (-1,-1), 8),
                ('RIGHTPADDING',  (0,0), (-1,-1), 8),
                ('BACKGROUND',    (0,0), (-1,-1), SURFACE2),
                ('BOX',           (0,0), (-1,-1), 0.5, BORDER),
            ]))
            story.append(img_table)

            # Captions
            cap_data = [[
                Paragraph('Original MRI Scan', caption_style),
                Paragraph('Grad-CAM Heatmap', caption_style),
            ]]
            cap_table = Table(cap_data, colWidths=[8.5*cm, 8.5*cm])
            cap_table.setStyle(TableStyle([
                ('ALIGN',       (0,0), (-1,-1), 'CENTER'),
                ('TOPPADDING',  (0,0), (-1,-1), 2),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(cap_table)
            story.append(Paragraph(
                'Red/yellow regions in the Grad-CAM heatmap indicate the areas '
                'that influenced the model\'s prediction most strongly.',
                ParagraphStyle('capnote', fontSize=8, textColor=TEXT_MUTED,
                               fontName='Helvetica', alignment=TA_CENTER,
                               spaceBefore=3, spaceAfter=6)
            ))

        else:
            # Only original MRI — centred
            img_row = [[RLImage(mri_path, width=IMG_W, height=IMG_H)]]
            img_table = Table(img_row, colWidths=[17*cm])
            img_table.setStyle(TableStyle([
                ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
                ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING',    (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('BACKGROUND',    (0,0), (-1,-1), SURFACE2),
                ('BOX',           (0,0), (-1,-1), 0.5, BORDER),
            ]))
            story.append(img_table)
            story.append(Paragraph('Original MRI Scan', caption_style))

        story.append(Spacer(1, 0.35*cm))

    # ══════════════════════════════════════════════════════════════
    # 5. PROBABILITY BREAKDOWN WITH DRAWN BARS
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph('Probability Breakdown', section_style))

    classes = [
        ('Glioma',     prediction.prob_glioma),
        ('Meningioma', prediction.prob_meningioma),
        ('No Tumor',   prediction.prob_notumor),
        ('Pituitary',  prediction.prob_pituitary),
    ]

    BAR_W = 190
    BAR_H = 11

    prob_header = [
        Paragraph('<b>Class</b>',       ParagraphStyle('ph', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_LEFT)),
        Paragraph('<b>Probability</b>', ParagraphStyle('ph', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph('<b>Confidence Bar</b>', ParagraphStyle('ph', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold', alignment=TA_LEFT)),
    ]

    prob_rows = [prob_header]
    for label, prob in classes:
        is_predicted = (
            prediction.has_tumor and
            prediction.tumor_type and
            label.lower().replace(' ', '') == prediction.tumor_type.lower().replace('_', '')
        ) or (not prediction.has_tumor and label == 'No Tumor')

        name_style = ParagraphStyle(
            'pn', fontSize=9,
            textColor=result_color if is_predicted else DARK,
            fontName='Helvetica-Bold' if is_predicted else 'Helvetica'
        )
        pct_style = ParagraphStyle(
            'pc', fontSize=9,
            textColor=result_color if is_predicted else PRIMARY,
            fontName='Helvetica-Bold', alignment=TA_CENTER
        )
        prob_rows.append([
            Paragraph(('▶ ' if is_predicted else '') + label, name_style),
            Paragraph(f'{prob * 100:.1f}%', pct_style),
            _prob_bar(prob, BAR_W, BAR_H),
        ])

    prob_table = Table(prob_rows, colWidths=[4.5*cm, 3*cm, 9.5*cm])
    prob_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  PRIMARY),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [LIGHT_BG, WHITE]),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('RIGHTPADDING',  (0,0), (-1,-1), 10),
        ('GRID',          (0,0), (-1,-1), 0.5, BORDER),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN',         (1,0), (1,-1),  'CENTER'),
    ]))
    story.append(prob_table)
    story.append(Spacer(1, 0.35*cm))

    # ══════════════════════════════════════════════════════════════
    # 6. MODEL INFORMATION
    # ══════════════════════════════════════════════════════════════
    story.append(Paragraph('Model Information', section_style))

    model_data = [
        ['Model', 'Architecture', 'Val Accuracy', 'Ensemble Weight'],
        ['VGG16',         'Deep CNN (16 layers)',        '93.69%', '36.65%'],
        ['ResNet50',      'Residual Network (50 layers)', '71.25%', '27.87%'],
        ['EfficientNetB0','Efficient Scaling CNN',        '90.69%', '35.48%'],
    ]
    model_table = Table(model_data, colWidths=[4*cm, 5.5*cm, 3.5*cm, 4*cm])
    model_table.setStyle(TableStyle([
        ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,0), (-1,-1), 8.5),
        ('TEXTCOLOR',     (0,0), (-1,0),  WHITE),
        ('BACKGROUND',    (0,0), (-1,0),  PRIMARY),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [LIGHT_BG, WHITE]),
        ('TOPPADDING',    (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('GRID',          (0,0), (-1,-1), 0.5, BORDER),
        ('ALIGN',         (2,0), (3,-1),  'CENTER'),
    ]))
    story.append(model_table)
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph(
        'Dataset: Masoud Nickparvar Brain Tumor MRI Dataset — 4 classes: '
        'Glioma, Meningioma, No Tumor, Pituitary. '
        'Ensemble prediction uses weighted average of all three model outputs.',
        ParagraphStyle('ds', fontSize=8.5, textColor=TEXT_MUTED,
                       fontName='Helvetica', spaceAfter=4, leading=13)
    ))
    story.append(Spacer(1, 0.2*cm))

    # ══════════════════════════════════════════════════════════════
    # 7. DISCLAIMER + FOOTER
    # ══════════════════════════════════════════════════════════════
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
    story.append(Spacer(1, 0.2*cm))

    disclaimer_data = [[
        Paragraph(
            '<b>Medical Disclaimer:</b> This report is generated by an AI system for '
            'educational and informational purposes only. It does not constitute a medical '
            'diagnosis and should not be used as a substitute for professional medical advice, '
            'diagnosis, or treatment. Always consult a qualified neurologist or medical '
            'professional. CerebroCare360 accepts no liability for decisions made based on '
            'this report.',
            disclaimer_style
        )
    ]]
    disclaimer_table = Table(disclaimer_data, colWidths=[17*cm])
    disclaimer_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), colors.HexColor('#fffbeb')),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING',   (0,0), (-1,-1), 12),
        ('RIGHTPADDING',  (0,0), (-1,-1), 12),
        ('BOX',           (0,0), (-1,-1), 1, colors.HexColor('#fde68a')),
    ]))
    story.append(disclaimer_table)
    story.append(Spacer(1, 0.25*cm))
    story.append(Paragraph(
        f'Generated by CerebroCare360  ·  '
        f'{datetime.utcnow().strftime("%d %B %Y at %H:%M UTC")}',
        muted_style
    ))

    doc.build(story)
    return f'reports/{user.id}/{filename}'