import os
import urllib.request
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image as RLImage, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# ── Company constants ──────────────────────────────────────────────────────────
COMPANY_NAME     = "Shreeji Ceramica"
COMPANY_TAGLINE  = "Redefining Luxury"
COMPANY_PHONE    = "+91 9033745455"
COMPANY_EMAIL    = "shreejiceramica303@gmail.com"
COMPANY_LOGO_URL = "https://www.shreejiceramica.com/tiles/vadodara-logo.png"

def _get_logo_path(base_dir):
    """Return local logo path; download from web if not already saved."""
    local = os.path.join(base_dir, "static", "shreeji_logo.png")
    if os.path.exists(local):
        return local
    try:
        os.makedirs(os.path.join(base_dir, "static"), exist_ok=True)
        urllib.request.urlretrieve(COMPANY_LOGO_URL, local)
        return local
    except Exception:
        return None

def generate_quote(data):
    """Generates a premium PDF quote matching the user's reference exactly."""
    show_bg_logo  = data.get("show_bg_logo", False)
    made_by       = str(data.get("made_by") or "").strip()
    made_by_phone = str(data.get("made_by_phone") or "").strip()
    quote_number  = data.get("quote_number", "")
    today_str     = datetime.now().strftime("%d %B %Y")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = _get_logo_path(base_dir)

    # ── Background watermark callback (Large Pictorial Logo) ─────────
    def draw_background(canvas, doc):
        page_w, page_h = A4
        if show_bg_logo and logo_path and os.path.exists(logo_path):
            canvas.saveState()
            canvas.setFillAlpha(0.12)  # Professional watermark opacity
            logo_w, logo_h = 420, 260
            canvas.drawImage(
                logo_path,
                (page_w - logo_w) / 2,
                (page_h - logo_h) / 2,
                width=logo_w,
                height=logo_h,
                preserveAspectRatio=True,
                mask='auto',
            )
            canvas.restoreState()

    # Document setup
    doc = SimpleDocTemplate("quotation.pdf", pagesize=A4,
                            rightMargin=30, leftMargin=30,
                            topMargin=20, bottomMargin=25)
    
    styles = getSampleStyleSheet()
    elements = []

    # ── 1. Header Branding section ──────────────────────────────────────────
    if show_bg_logo:
        # A. Brand Logos (Aquant, Kohler, Plumber)
        def _brand_img(b_name, filename, w=48, h=25):
            p = os.path.join(base_dir, "static", filename)
            # Fallback if specific brand files missing/broken
            if b_name == 'AQUANT' and (not os.path.exists(p) or os.path.getsize(p) < 100):
                 p = os.path.join(base_dir, "static", "gen_aquant.png")
            if b_name == 'KOHLER' and (not os.path.exists(p) or os.path.getsize(p) < 100):
                 p = os.path.join(base_dir, "static", "gen_kohler.png")
            if b_name == 'PLUMBER' and (not os.path.exists(p) or os.path.getsize(p) < 100):
                 p = os.path.join(base_dir, "static", "gen_plumber.png")
            
            if os.path.exists(p) and os.path.getsize(p) > 500:
                try: return RLImage(p, width=w, height=h, kind='proportional')
                except: pass
            
            brand_style = ParagraphStyle('bs', parent=styles['Normal'], fontSize=7, alignment=1)
            return Table([[Paragraph(f"<b>{b_name}</b>", brand_style)]], colWidths=[w])

        aquant_img  = _brand_img('AQUANT', "brand_aquant.png")
        kohler_img  = _brand_img('KOHLER', "brand_kohler.png")
        plumber_img = _brand_img('PLUMBER', "brand_plumber.png")
        
        brands_row = Table([[aquant_img, kohler_img, plumber_img]], colWidths=[55, 55, 55])
        brands_row.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))

        # B. Showroom Info (Center-Right)
        name_style = ParagraphStyle('N', parent=styles['Normal'], fontSize=22, fontName='Helvetica-Bold', textColor=colors.HexColor("#334155"), alignment=2, leading=26)
        tag_style = ParagraphStyle('T', parent=styles['Normal'], fontSize=10, fontName='Helvetica-BoldOblique', textColor=colors.HexColor("#eab308"), alignment=2, leading=14)
        contact_style = ParagraphStyle('C', parent=styles['Normal'], fontSize=8.5, textColor=colors.HexColor("#64748b"), alignment=2, leading=12)

        info_cell = [
            Paragraph(COMPANY_NAME, name_style),
            Spacer(1, 2),
            Paragraph(COMPANY_TAGLINE, tag_style),
            Spacer(1, 2),
            Paragraph(f"Ph: {COMPANY_PHONE} | {COMPANY_EMAIL}", contact_style),
        ]

        # C. Pictorial Logo (Far Right)
        shreeji_logo = ""
        if logo_path and os.path.exists(logo_path):
            shreeji_logo = RLImage(logo_path, width=75, height=55, kind='proportional')

        # Assemble Header Table
        header_table = Table([[brands_row, info_cell, shreeji_logo]], colWidths=[175, 255, 80])
        header_table.setStyle(TableStyle([
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
            ('LINEAFTER',  (0, 0), (0,  0),   0.5, colors.lightgrey), # Vertical separator
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING',(0,0), (-1,-1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 4))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#be1e2d"), spaceAfter=10))
    else:
        elements.append(Spacer(1, 40))

    # ── 2. Title & Quotation Meta section ────────────────────────────────────
    if show_bg_logo:
        title_style = ParagraphStyle('TS', parent=styles['Normal'], fontSize=20, fontName='Helvetica-Bold', textColor=colors.HexColor("#e0a020"), alignment=0) # Gold/Yellow Left Aligned
        
        meta_style = ParagraphStyle('MS', parent=styles['Normal'], fontSize=8.5, fontName='Helvetica-Bold', alignment=2, leading=11)
        quote_id = quote_number if quote_number else f"SC-{today_str.replace(' ', '')}"
        meta_text = [f"<b>No:</b> {quote_id}", f"<b>Date:</b> {today_str}"]
        if made_by:
            meta_text.append(f"<b>Prepared By: {made_by} - {made_by_phone}</b>" if made_by_phone else f"<b>Prepared By: {made_by}</b>")
        
        meta_para = Paragraph("<br/>".join(meta_text), meta_style)
        
        title_table = Table([[Paragraph("<b>BUSINESS PROPOSAL</b>", title_style), meta_para]], colWidths=[330, 185])
        title_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
        
        elements.append(title_table)
        elements.append(Spacer(1, 10))
    else:
        # Simple title when branding is off
        title_style = ParagraphStyle('TS_Plain', parent=styles['Normal'], fontSize=18, fontName='Helvetica-Bold', textColor=colors.black, alignment=1)
        elements.append(Paragraph("QUOTATION", title_style))
        elements.append(Spacer(1, 15))

    # ── 3. Bill To section ────────────────────────────────────────────────
    label_s = ParagraphStyle('L', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', textColor=colors.HexColor("#334155"), leading=13)
    val_s = ParagraphStyle('V', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#64748b"), leading=13)
    
    client_data = [
        [Paragraph("Client Name:", label_s), Paragraph(data.get('client_name', 'Customer Name'), val_s)],
        [Paragraph("Mobile No:", label_s),   Paragraph(data.get('mobile', '-'), val_s)],
        [Paragraph("Company:", label_s),      Paragraph(data.get('company', '-'), val_s)],
        [Paragraph("Address:", label_s),      Paragraph(data.get('address', '-'), val_s)],
    ]
    bill_table = Table(client_data, colWidths=[85, 400])
    bill_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
    elements.append(bill_table)
    elements.append(Spacer(1, 25))

    # ── 4. Items Table section ─────────────────────────────────────────────
    # Reverting to EXACT image format: S.No, Image, Item Description, Qty, Price, Disc(%), Amount
    header_row = ["S.No", "Image", "Item Description", "Qty", "Price", "Disc(%)", "Amount"]
    table_data = [header_row]
    
    for idx, item in enumerate(data.get("items", [])):
        qty   = int(item.get("quantity") or 1)
        price = float(item.get("price") or 0)
        disc  = float(item.get("discount") or 0)
        total = qty * price
        amount = total - (total * disc / 100)
        
        # Image object
        img_obj = ""
        img_p = item.get("image")
        if img_p and img_p.startswith("/static/images/"):
            real_p = os.path.join(base_dir, img_p.lstrip("/"))
            if os.path.exists(real_p):
                img_obj = RLImage(real_p, width=45, height=45)
        
        # Description styling
        raw = item.get("rawText", item.get("name", "Unknown Item"))
        parts = raw.split("\n", 1)
        name_str = parts[0].strip().replace("&", "&amp;")
        desc_str = parts[1].replace("\n", "<br/>").replace("&", "&amp;") if len(parts) > 1 else ""
        desc_para = Paragraph(f"<b>{name_str}</b><br/>{desc_str}", ParagraphStyle('P', parent=styles['Normal'], fontSize=8.5, leading=10))
        
        table_data.append([str(idx+1), img_obj, desc_para, str(qty), f"{price:,.2f}", f"{disc:g}%" if disc > 0 else "-", f"{amount:,.2f}"])

    # Totals Section
    subtotal = float(data.get("subtotal", 0))
    gst_rate = float(data.get("gst_rate", 0))
    gst_amt  = float(data.get("gst_amount", 0))
    grand    = float(data.get("grand_total", 0))
    
    table_data.append(["", "", "", "Subtotal:", f"Rs {subtotal:,.2f}", "", ""])
    table_data.append(["", "", "", f"GST ({gst_rate:g}%):", f"+ Rs {gst_amt:,.2f}", "", ""])
    table_data.append(["", "", "", "Grand Total:", f"Rs {grand:,.2f}", "", ""])

    # Table Appearance
    col_w = [30, 60, 230, 45, 65, 45, 75]
    t = Table(table_data, colWidths=col_w)
    
    t_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")), # Light Header
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (2,1), (2,-len(table_data)), 'LEFT'),
        ('ALIGN', (4,1), (-1,-len(table_data)), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
        ('BOX', (0,0), (-1,-1), 0.25, colors.lightgrey),
    ])
    
    # Custom Footer Styling
    n_items = len(data.get("items", []))
    for r in range(n_items+1, len(table_data)):
        t_style.add('SPAN', (0,r), (2,r)) # Merge left
        t_style.add('SPAN', (4,r), (6,r)) # Merge right for values
        t_style.add('ALIGN', (3,r), (3,r), 'RIGHT')
        t_style.add('ALIGN', (4,r), (4,r), 'RIGHT')
        t_style.add('FONTNAME', (3,r), (-1,r), 'Helvetica-Bold')
        t_style.add('BACKGROUND', (0,r), (-1,r), colors.white)
        
    t_style.add('TEXTCOLOR', (4, -1), (-1, -1), colors.HexColor("#0284c7")) # Grand total blue
    t.setStyle(t_style)
    elements.append(t)
    elements.append(Spacer(1, 40))

    # ── 5. Footer & Signatory section ────────────────────────────────────
    if show_bg_logo:
        terms_title = ParagraphStyle('TT', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', textColor=colors.HexColor("#1e293b"), spaceAfter=8)
        terms_text = ParagraphStyle('TX', parent=styles['Normal'], fontSize=8, leading=12, textColor=colors.HexColor("#475569"))
        
        terms = [
            Paragraph("Terms & Conditions:", terms_title),
            Paragraph("1. Quotation is valid for 15 days from the issued date.", terms_text),
            Paragraph("2. 100% advance payment required along with the purchase order.", terms_text),
            Paragraph("3. Goods once sold will not be taken back or exchanged.", terms_text),
            Paragraph("4. Subject to local jurisdiction only.", terms_text),
        ]
        
        sig_style = ParagraphStyle('S1', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', alignment=2)
        sig_line = ParagraphStyle('S2', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', alignment=2, spaceBefore=45)
        
        signatory = [Paragraph("For Shreeji Ceramica", sig_style), Paragraph("Authorized Signatory", sig_line)]
        
        foot_table = Table([[terms, signatory]], colWidths=[300, 215])
        foot_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'BOTTOM'), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
        elements.append(foot_table)

    # Build
    doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)
