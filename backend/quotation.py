import os
import urllib.request
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image as RLImage, HRFlowable, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# ── Company constants ──────────────────────────────────────────────────────────
COMPANY_NAME     = "Shreeji Ceramica"
COMPANY_TAGLINE  = "Redefining Luxury"
COMPANY_PHONE    = "9033745455"
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
    show_bg_logo  = data.get("show_bg_logo", False)
    made_by       = str(data.get("made_by") or "").strip()
    made_by_phone = str(data.get("made_by_phone") or "").strip()
    made_by_email = str(data.get("made_by_email") or "").strip()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = _get_logo_path(base_dir)

        # ── Background watermark callback (draws on every page) ─────────
    def draw_background(canvas, doc):
        from reportlab.lib.pagesizes import A4
        page_w, page_h = A4

        # Background logo watermark
        if show_bg_logo and logo_path and os.path.exists(logo_path):
            canvas.saveState()
            canvas.setFillAlpha(0.30)   # 30% opacity – clearly visible but still watermark
            logo_w, logo_h = 340, 190
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

    doc = SimpleDocTemplate("quotation.pdf", pagesize=A4,
                            rightMargin=30, leftMargin=30,
                            topMargin=30, bottomMargin=30)

    styles = getSampleStyleSheet()
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # ── Custom styles ──────────────────────────────────────────────────────────
    company_name_style = ParagraphStyle(
        'CompanyName',
        parent=styles['Normal'],
        fontSize=18,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor("#2c2c2c"),
        leading=22,
        spaceAfter=2,
    )
    company_tagline_style = ParagraphStyle(
        'CompanyTagline',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor("#e0a020"),
        leading=12,
        spaceAfter=2,
    )
    company_contact_style = ParagraphStyle(
        'CompanyContact',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor("#555555"),
        leading=13,
    )
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor("#be1e2d"),
        spaceAfter=10,
        spaceBefore=14,
        alignment=1,
        fontName='Helvetica-Bold',
    )
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=22,
        textColor=colors.dimgrey,
        spaceAfter=5
    )

    elements = []

    # ── Company Header: Name (LEFT)  |  Details + Brand Logos + ShreejiLogo (RIGHT) ──
    logo_path = _get_logo_path(base_dir)
    shreeji_logo_cell = ""
    if logo_path and os.path.exists(logo_path):
        shreeji_logo_cell = RLImage(logo_path, width=80, height=55, kind='proportional')

    # Brand logo helper
    def _brand_img(b_name, filename, w=48, h=25):
        # We try to load generic high-quality PIL images we generated 
        p = os.path.join(base_dir, "static", filename)
        # If the file is 19 bytes (broken aquant) or missing, we use our generated ones
        if b_name == 'AQUANT' and (not os.path.exists(p) or os.path.getsize(p) < 100):
             p = os.path.join(base_dir, "static", "gen_aquant.png")
        if b_name == 'KOHLER' and (not os.path.exists(p) or os.path.getsize(p) < 100):
             p = os.path.join(base_dir, "static", "gen_kohler.png")
        if b_name == 'PLUMBER' and (not os.path.exists(p) or os.path.getsize(p) < 100):
             p = os.path.join(base_dir, "static", "gen_plumber.png")
        
        if os.path.exists(p) and os.path.getsize(p) > 500:
            try:
                return RLImage(p, width=w, height=h, kind='proportional')
            except Exception:
                pass
        
        # Last resort: text block
        brand_style = ParagraphStyle('bstyle', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor("#FFFFFF"), alignment=1)
        # Return a colored block with text
        t = Table([[Paragraph(f"<b>{b_name}</b>", brand_style)]], colWidths=[w], rowHeights=[h])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#1e293b")), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        return t

    aquant_cell  = _brand_img('AQUANT', "brand_aquant.png",  w=52, h=28)
    kohler_cell  = _brand_img('KOHLER', "brand_kohler.png",  w=52, h=28)
    plumber_cell = _brand_img('PLUMBER',"brand_plumber.png", w=52, h=28)

    # Contact cell (stacked text, right-aligned)
    contact_style = ParagraphStyle(
        'ContactRight',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor("#555555"),
        leading=14,
        alignment=2,   # right
    )
    
    # Company info cell (Name, Tagline, Contact grouped together and right-aligned)
    company_name_style.alignment = 2  # Right-align company name
    company_tagline_style.alignment = 2  # Right-align tagline
    
    company_info_cell = [
        Paragraph(COMPANY_NAME, company_name_style),
        Paragraph(COMPANY_TAGLINE, company_tagline_style),
        Spacer(1, 4),
        Paragraph(f"Ph: {COMPANY_PHONE}  |  {COMPANY_EMAIL}", contact_style),
    ]

    # Table: [Aquant | Kohler | Plumber | Company Info | ShreejiLogo]
    header_table = Table(
        [[aquant_cell, kohler_cell, plumber_cell, company_info_cell, shreeji_logo_cell]],
        colWidths=[58, 58, 58, 275, 86],
    )
    header_table.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',         (0, 0), (2,  0),  'CENTER'),    # Brands logo center
        ('ALIGN',         (3, 0), (3,  0),  'RIGHT'),     # Company info right-aligned
        ('ALIGN',         (4, 0), (4,  0),  'RIGHT'),     # Shreeji logo right-aligned
        ('LEFTPADDING',   (0, 0), (-1, -1), 2),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 2),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        # Subtle divider between company info and logos
        ('LINEBEFORE',    (3, 0), (3,  0),   0.5, colors.HexColor("#e2e8f0")),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=1.5,
                                color=colors.HexColor("#be1e2d"), spaceAfter=6))

    # ── QUOTATION title + number + date ───────────────────────────────────────
    from datetime import datetime
    quote_number = data.get("quote_number", "")
    today_str = datetime.now().strftime("%d %B %Y")

    quote_meta_style = ParagraphStyle(
        'QuoteMeta',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        alignment=2,  # Right-aligned so it aligns with Shreeji Logo
        leading=14,
    )

    # Setup text for Made By
    made_by_str = ""
    contact_details = ""
    if made_by:
        # We will just show "Made by: Name"
        made_by_str = f"<br/><br/><font size=8 color='#64748b'>Made by: <b><u>{made_by}</u></b></font>"

        # Combine details for the pop-up note
        lines = [f"Name: {made_by}"]
        if made_by_phone: lines.append(f"Phone: {made_by_phone}")
        if made_by_email: lines.append(f"Email: {made_by_email}")
        contact_details = chr(10).join(lines)  # newline separated

    # Create a custom flowable that draws the Annotation when placed in the table
    class AnnotationFlowable(Flowable):
        def __init__(self, annotation_text):
            Flowable.__init__(self)
            self.annotation_text = annotation_text
            self.width = 1
            self.height = 1

        def draw(self):
            # Create a Text Annotation (PDF Pop-up Note) at current coordinate
            if self.annotation_text:
                self.canv.textAnnotation(self.annotation_text, Rect=(0, 0, 15, 15))

    title_cell = [Paragraph("<b>QUOTATION</b>", title_style)]
    
    meta_cell = [Paragraph(f"<b>No:</b> {quote_number}<br/><b>Date:</b> {today_str}{made_by_str}", quote_meta_style)]
    if contact_details:
        # Append the invisible annotation flowable so the pop-up shows over the date cell
        meta_cell.append(AnnotationFlowable(contact_details))

    title_row = Table(
        [[title_cell, meta_cell]],
        colWidths=[380, 125],
    )
    title_row.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING',   (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 2),
    ]))
    elements.append(title_row)
    
    info_lines = []
    if data.get('client_name'):
        info_lines.append(f"<b>Client Name:</b> {data.get('client_name')}")
    if data.get('mobile'):
        info_lines.append(f"<b>Mobile No:</b> {data.get('mobile')}")
    if data.get('company'):
        info_lines.append(f"<b>Company:</b> {data.get('company')}")
    if data.get('gst'):
        info_lines.append(f"<b>GSTIN:</b> {data.get('gst')}")
    if data.get('address'):
        info_lines.append(f"<b>Address:</b> {data.get('address')}")
        
    client_info = "<br/>".join(info_lines) if info_lines else "<b>Client Details:</b> N/A"
    elements.append(Paragraph(client_info, header_style))
    elements.append(Spacer(1, 20))
    
    # Table Data
    table_data = [["S.No", "Image", "Item Description", "Qty", "Price", "Disc(%)", "Amount"]]
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    for idx, item in enumerate(data.get("items", [])):
        qty = int(item.get("quantity") or 1)
        price = float(item.get("price") or 0)
        disc = float(item.get("discount") or 0)
        total = qty * price
        amount = total - (total * disc / 100)
        
        # Parse Image
        img_obj = ""
        img_path = item.get("image")
        if img_path and img_path.startswith("/static/images/"):
            real_img_path = os.path.join(base_dir, img_path.lstrip("/"))
            if os.path.exists(real_img_path):
                img_obj = RLImage(real_img_path, width=45, height=45)
                
        # Parse Raw Text
        raw_text = item.get("rawText", item.get("name", "Unknown Item"))
        escaped_text = raw_text.replace("\n", "<br/>").replace("&", "&amp;")
        desc_para = Paragraph(f"<font size=8>{escaped_text}</font>", styles['Normal'])
        
        table_data.append([
            str(idx + 1),
            img_obj,
            desc_para,
            str(qty),
            f"{price:,.2f}",
            f"{disc:g}%" if disc > 0 else "-",
            f"{amount:,.2f}"
        ])
    
    # Totals Calculation
    subtotal = float(data.get("subtotal", 0))
    discount_percent = float(data.get("discount_percent", 0))
    discount_amount = float(data.get("discount_amount", 0))
    taxable_amount = float(data.get("taxable_amount", 0))
    gst_rate = float(data.get("gst_rate", 0))
    gst_amount = float(data.get("gst_amount", 0))
    grand_total = float(data.get("grand_total", 0))
    
    # Footer rows for table
    table_data.append(["", "", "", "", "", "Subtotal:", f"Rs {subtotal:,.2f}"])
    if discount_percent > 0:
        table_data.append(["", "", "", "", "", f"Discount ({discount_percent:g}%):", f"- Rs {discount_amount:,.2f}"])
        table_data.append(["", "", "", "", "", "Taxable Value:", f"Rs {taxable_amount:,.2f}"])
    
    if gst_rate > 0:
        table_data.append(["", "", "", "", "", f"GST ({gst_rate:g}%):", f"+ Rs {gst_amount:,.2f}"])
        
    table_data.append(["", "", "", "", "", "Grand Total:", f"Rs {grand_total:,.2f}"])
    
    # Table Styling
    col_widths = [30, 55, 185, 40, 70, 50, 105]
    t = Table(table_data, colWidths=col_widths)
    
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),  # Left align item description
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'), # Right align prices and amounts
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.lightgrey),
    ])
    
    # Format the footer rows specially
    num_items = len(data.get("items", []))
    footer_start_row = num_items + 1
    
    # We want to span the first 5 columns for footer rows to hide empty grid squares
    for row in range(footer_start_row, len(table_data)):
        table_style.add('SPAN', (0, row), (4, row)) 
        
    table_style.add('LINEBELOW', (0, footer_start_row-1), (-1, footer_start_row-1), 1, colors.HexColor("#cbd5e1"))
    table_style.add('FONTNAME', (5, footer_start_row), (5, -1), 'Helvetica-Bold')
    table_style.add('FONTNAME', (6, -1), (6, -1), 'Helvetica-Bold')
    table_style.add('BACKGROUND', (5, -1), (6, -1), colors.HexColor("#f8fafc"))
    table_style.add('TEXTCOLOR', (6, -1), (6, -1), colors.HexColor("#0284c7"))
    
    t.setStyle(table_style)
    elements.append(t)
    elements.append(Spacer(1, 15))



    doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)
