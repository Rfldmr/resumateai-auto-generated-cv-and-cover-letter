from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

def generate_ats_cv(data, filename="static/generated_cv.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    
    styles = getSampleStyleSheet()
    story = []

    # --- CUSTOM STYLES (Meniru Template) ---
    style_name = ParagraphStyle('Name', parent=styles['Heading1'], alignment=TA_CENTER, fontName='Times-Bold', fontSize=16, spaceAfter=6)
    style_contact = ParagraphStyle('Contact', parent=styles['Normal'], alignment=TA_CENTER, fontName='Times-Roman', fontSize=10)
    style_summary = ParagraphStyle('Summary', parent=styles['Normal'], alignment=TA_JUSTIFY, fontName='Times-Roman', fontSize=11, leading=14)
    
    # Style Header Section (Garis Bawah Tebal)
    style_section_head = ParagraphStyle('Section', parent=styles['Heading2'], fontName='Times-Bold', fontSize=11, spaceBefore=12, spaceAfter=2, textTransform='uppercase')
    
    # Style Item (Jabatan & Perusahaan)
    style_item_title = ParagraphStyle('ItemTitle', parent=styles['Normal'], fontName='Times-Bold', fontSize=11)
    style_item_date = ParagraphStyle('ItemDate', parent=styles['Normal'], fontName='Times-Roman', fontSize=11, alignment=TA_RIGHT)
    
    # Style Bullet Point
    style_bullet = ParagraphStyle('Bullet', parent=styles['Normal'], fontName='Times-Roman', fontSize=11, leftIndent=15, firstLineIndent=0, bulletIndent=0)
    style_no_indent = ParagraphStyle('NoIndent', parent=styles['Normal'], fontName='Times-Roman', fontSize=11, leftIndent=0)

    # --- 1. HEADER ---
    story.append(Paragraph(data['full_name'], style_name))
    contact_text = f"{data['email']} | {data['phone']} | {data['city']}, {data['country']}"
    story.append(Paragraph(contact_text, style_contact))
    story.append(Spacer(1, 10))

    # --- 2. SUMMARY ---
    # Menggunakan summary hasil generate AI atau input user
    if data.get('summary'):
        story.append(Paragraph(data['summary'], style_summary))
        story.append(Spacer(1, 10))

    # Helper function untuk Garis Horizontal
    def add_line():
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=2, spaceAfter=8))

    # --- 3. PENGALAMAN KERJA ---
    if data.get('experience'):
        story.append(Paragraph("PENGALAMAN KERJA", style_section_head))
        add_line()
        
        for exp in data['experience']:
            # Baris 1: Posisi, Perusahaan (Kiri) -- Tanggal (Kanan)
            # Kita pakai Table untuk layout kiri-kanan
            title_text = f"<b>{exp['role']}</b>, {exp['company']}"
            date_text = f"{exp['start_date']} – {exp['end_date']}"
            
            data_row = [[Paragraph(title_text, style_item_title), Paragraph(date_text, style_item_date)]]
            t = Table(data_row, colWidths=[350, 140])
            t.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT'), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
            story.append(t)
            
            # Jobdesc Bullets
            for desc in exp['description_points']:
                story.append(Paragraph(f"• {desc}", style_bullet))
            story.append(Spacer(1, 6))

    # --- 4. PENDIDIKAN ---
    if data.get('education'):
        story.append(Paragraph("PENDIDIKAN", style_section_head))
        add_line()
        
        for edu in data['education']:
            title_text = f"<b>{edu['major']}</b>, {edu['institution']}"
            date_text = f"{edu['start_date']} – {edu['end_date']}"
            
            data_row = [[Paragraph(title_text, style_item_title), Paragraph(date_text, style_item_date)]]
            t = Table(data_row, colWidths=[350, 140])
            t.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT')]))
            story.append(t)
            
            # Opsional: IPK atau Aktivitas
            if edu.get('description'):
                story.append(Paragraph(f"• {edu['description']}", style_bullet))
            story.append(Spacer(1, 6))

    # --- 5. ORGANISASI ---
    if data.get('organization'):
        story.append(Paragraph("PENGALAMAN ORGANISASI", style_section_head))
        add_line()
        
        for org in data['organization']:
            title_text = f"<b>{org['role']}</b>, {org['org_name']}"
            date_text = f"{org['start_date']} – {org['end_date']}"
            
            data_row = [[Paragraph(title_text, style_item_title), Paragraph(date_text, style_item_date)]]
            t = Table(data_row, colWidths=[350, 140])
            t.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT')]))
            story.append(t)
            
            for desc in org['description_points']:
                story.append(Paragraph(f"• {desc}", style_bullet))
            story.append(Spacer(1, 6))

    # --- 6. PENGHARGAAN ---
    if data.get('awards'):
        story.append(Paragraph("PENGHARGAAN", style_section_head))
        add_line()
        for aw in data['awards']:
             # Layout: Nama (Kiri), Tahun (Kanan)
            data_row = [[Paragraph(f"<b>• {aw['name']}</b>", style_no_indent), Paragraph(aw['year'], style_item_date)]]
            t = Table(data_row, colWidths=[350, 140])
            t.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT')]))
            story.append(t)
            
            if aw.get('description'):
                story.append(Paragraph(f"  {aw['description']}", ParagraphStyle('Indented', parent=style_no_indent, leftIndent=15)))

    # --- 7. KETERAMPILAN (2 Kolom) ---
    if data.get('skills'):
        story.append(Spacer(1, 10))
        story.append(Paragraph("KETERAMPILAN", style_section_head))
        add_line()
        
        # Format list string menjadi bullet paragraph
        soft_content = [Paragraph("<b>Soft Skills:</b>", style_no_indent)] + [Paragraph(f"• {s}", style_no_indent) for s in data['skills']['soft']]
        hard_content = [Paragraph("<b>Hard Skills:</b>", style_no_indent)] + [Paragraph(f"• {s}", style_no_indent) for s in data['skills']['hard']]
        
        # Membuat tabel 2 kolom transparan
        data_row = [[soft_content, hard_content]]
        t = Table(data_row, colWidths=[245, 245])
        t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        story.append(t)

    doc.build(story)
    return filename