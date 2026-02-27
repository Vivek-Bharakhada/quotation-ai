import fitz  # PyMuPDF
import os
import re


def clean_text(text):
    """Clean PDF-extracted text: fix encodings, spaces, and word boundaries."""
    import unicodedata

    text = unicodedata.normalize("NFKC", text)

    unicode_spaces = [
        '\u00a0', '\u2000', '\u2001', '\u2002', '\u2003', '\u2004',
        '\u2005', '\u2006', '\u2007', '\u2008', '\u2009', '\u200a',
        '\u202f', '\u205f', '\u3000', '\u00ad', '\ufeff'
    ]
    for sp in unicode_spaces:
        text = text.replace(sp, ' ')

    # Replace control chars (including chr(3) used in some PDFs as word separator)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', text)
    text = re.sub(r'[\u200b-\u200f\u2028\u2029]', '', text)
    # chr(3) is the nasty one — it joins words without spaces in Aquant PDFs
    text = text.replace('\x03', ' ')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_content(pdf_path, max_pages=None):
    doc = fitz.open(pdf_path)
    content_list = []

    image_dir = os.path.join("static", "images")
    os.makedirs(image_dir, exist_ok=True)

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    pdf_prefix = re.sub(r'[^a-zA-Z0-9_]', '_', pdf_name)[:20]

    num_pages = len(doc)
    if max_pages: num_pages = min(num_pages, max_pages)

    current_category = None
    brand = "Aquant" if "aquant" in pdf_name.lower() else "Kohler" if "kohler" in pdf_name.lower() else "Generic"

    for page_num in range(num_pages):
        page = doc[page_num]

        # ── 1. Extract images with their bounding boxes ──────────────────
        img_records = []
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            # Skip if image width/height is too small (likely icons or decorative elements)
            # img is (xref, smask, width, height, bpc, colorspace, ...)
            width = img[2]
            height = img[3]
            if width < 50 or height < 50:
                continue

            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n > 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                
                img_filename = f"{pdf_prefix}_p{page_num}_i{img_index}.jpg"
                img_path = os.path.join(image_dir, img_filename)
                if not os.path.exists(img_path):
                    pix.save(img_path)
                
                rects = page.get_image_rects(xref)
                rect = rects[0] if rects else None
                img_records.append({"path": f"/static/images/{img_filename}", "rect": rect})
                pix = None
            except Exception:
                continue

        # ── 1.5. Kohler Extraction Logic ─────────────────────
        def map_kohler_category(text):
            t = text.upper()
            if "FRENCH GOLD" in t: return "French Gold"
            if "BRUSHED BRONZE" in t: return "Brushed Bronze"
            if "MATE BLACK" in t or "MATTE BLACK" in t: return "Matte Black"
            if "BRUSHED ROSE GOLD" in t: return "Brushed Rose Gold"
            if "ROSE GOLD" in t: return "Rose Gold"
            if "VIBRANT" in t or "VIBRANT STAINLESS" in t: return "Vibrant Finishes"
            
            if "SMART TOILET" in t or "C3" in t or "BIDET" in t or "CLEANSING SEAT" in t:
                return "Smart Toilets & Bidet Seats"
            if "WALL HUNG TOILET" in t or "1 PC TOILET" in t or "ONE-PIECE" in t or "WALL HUNG" in t or "WALL-HUNG" in t or "ESCALE" in t or "VEIL" in t or "TRACE" in t:
                return "1 pc Toilets & Wall Hungs"
            if "IN-WALL TANK" in t or "IN-WALL" in t or "CONCEALED CISTERN" in t or "CONCEALED TANK" in t or "DUAL FLUSH TANK" in t or "TANK ONLY" in t:
                return "In-Wall Tanks"
            if "FACEPLATE" in t or "PNEUMATIC" in t or "FLUSH VALVE" in t:
                return "Faceplates"
            if "TOILET" in t: return "Toilets"
            
            if "MIRROR" in t: return "Mirrors"
            if "VANIT" in t: return "Vanities"
            if "WASH BASIN" in t or "VESSEL" in t or "LAVATOR" in t or "PEDESTAL" in t or "BASIN" in t: return "Wash Basins"
            
            if "CLEANING SOLUTION" in t or "CLEANI" in t or "CLEANER" in t: return "Cleaning Solutions"
            if "KITCHEN" in t or "SINK" in t: return "Kitchen Sinks & Faucets"
            if "STEAM" in t: return "Steam"
            if "ENCLOSURE" in t or "LIB" in t or "SINGULIER" in t or "GLASS" in t: return "Shower Enclosures"
            if "SHOWERING" in t or "SHOWER" in t or "BATH AND SHOWER" in t or "BATH & SHOWER" in t: return "Showering"
            if "BATHTUB" in t or "BATH FILLER" in t or "BATH SPOUT" in t: return "Bathtubs & Bath Fillers"
            
            if "FAUCET" in t or "SPOUT" in t or "MIXER" in t or "TAP" in t: return "Faucets"
            if "ACCESSOR" in t or "TOWEL" in t or "BRUSH HOLDER" in t or "ROBE HOOK" in t: return "Accessories"
            if "COMMERCIAL" in t: return "Commercial Products"
            if "FITTING" in t: return "Fittings"
            
            return None

        # Kohler model codes are consistently hyphenated (e.g. K-1063956, K-24149IN-F-BN).
        kohler_code_re = re.compile(r'\bK\s*-\s*[A-Z0-9]+(?:-[A-Z0-9]+)*\b', re.IGNORECASE)

        def normalize_kohler_code(raw):
            return re.sub(r'\s+', '', str(raw or '')).upper()

        if brand == "Kohler":
            blocks = page.get_text("blocks")
            blocks.sort(key=lambda b: (b[1], b[0]))
            page_items = []
            
            last_name = ""
            for b in blocks:
                if b[6] != 0: continue
                text = b[4].strip()
                t_clean = text.replace('\n', ' ')
                x0, y0, x1, y1 = b[:4]

                if "CLEANING SOLUTIONS" in t_clean.upper():
                    current_category = "Cleaning Solutions"
                    continue
                
                # Check Header
                if y0 < 220:
                    mapped = map_kohler_category(t_clean)
                    if mapped:
                        current_category = mapped
                        continue
                
                if x0 < 90 and len(text) < 50 and not 'MRP' in text:
                    last_name = text.replace('\n', ' ')
                    continue

                code_match = kohler_code_re.search(text)
                if code_match and "MRP" in text.upper():
                        
                        t_comp = re.sub(r'[\s/\-]+', '', text)
                        price_match = re.search(r'(?:MRP|`|₹)[:.]?`?([\d,]{4,})', t_comp, re.IGNORECASE)
                        price = price_match.group(1).replace(",", "").strip() if price_match else "0"
                        
                        code = normalize_kohler_code(code_match.group(0))
                        
                        cx = (x0 + x1) / 2
                        cy = (y0 + y1) / 2
                        
                        best_img_idx = -1
                        best_dist = float("inf")
                        for i_idx, ir in enumerate(img_records):
                            if ir["rect"] is None: continue
                            img_rect = ir["rect"]
                            img_cx = (img_rect.x0 + img_rect.x1) / 2
                            img_cy = (img_rect.y0 + img_rect.y1) / 2
                            
                            dx = abs(img_cx - cx)
                            dy = img_cy - cy
                            
                            v_penalty = 0
                            if dy > 50: v_penalty = 300 
                            if dy < -400: v_penalty = 200
                
                            dist = (dx**2 + dy**2)**0.5 + v_penalty
                            if dist < best_dist and dist < 800:
                                best_dist = dist
                                best_img_idx = i_idx
                                
                        img_path = img_records[best_img_idx]["path"] if best_img_idx != -1 else ""
                        
                        prod_name = last_name + " - " + text.split('\n')[0][:100] if last_name else text.split('\n')[0][:100]
                        if current_category == "Cleaning Solutions":
                            inferred_category = "Cleaning Solutions"
                        else:
                            inferred_category = map_kohler_category(f"{last_name} {text}") or current_category or "Uncategorized"
                            
                        page_items.append({
                            "text": text,
                            "name": prod_name,
                            "price": price,
                            "page": page_num + 1,
                            "source": pdf_name,
                            "images": [img_path] if img_path else [],
                            "brand": brand,
                            "category": inferred_category
                        })
            if (not page_items) and any("SKU CODE" in str(b[4]).upper() for b in blocks if b[6] == 0):
                parsed_blocks = []
                page_mid_x = page.rect.width / 2.0
                for b in blocks:
                    if b[6] != 0:
                        continue
                    x0, y0, x1, y1 = b[:4]
                    raw_text = b[4].strip()
                    if not raw_text:
                        continue
                    normalized_text = " ".join([ln.strip() for ln in raw_text.splitlines() if ln.strip()])
                    upper = normalized_text.upper()
                    parsed_blocks.append({
                        "x0": x0,
                        "y0": y0,
                        "x1": x1,
                        "y1": y1,
                        "text": normalized_text,
                        "upper": upper,
                        "col": 0 if x0 < page_mid_x else 1
                    })

                def is_meta(upper_text):
                    if not upper_text:
                        return True
                    if upper_text.isdigit():
                        return True
                    if upper_text.startswith(("QTY:", "FORMAT:", "USAGE AREA:", "SKU CODE", "MRP")):
                        return True
                    if upper_text in {"KOHLER", "CLEANING SOLUTIONS"}:
                        return True
                    if "GENTLE ON FINISHES" in upper_text:
                        return True
                    return False

                seen_codes = set()
                for sb in parsed_blocks:
                    if "SKU CODE" not in sb["upper"]:
                        continue

                    code_match = re.search(r'SKU\s*CODE\s*[:\-]?\s*([A-Z0-9-]+)', sb["text"], re.IGNORECASE)
                    if not code_match:
                        continue
                    sku_code = code_match.group(1).upper()
                    if sku_code in seen_codes:
                        continue
                    seen_codes.add(sku_code)

                    sku_y = sb["y0"]
                    col = sb["col"]
                    mrp_candidates = [
                        x for x in parsed_blocks
                        if x["col"] == col and x["y0"] >= (sku_y - 4) and "MRP" in x["upper"] and (x["y0"] - sku_y) <= 90
                    ]
                    if not mrp_candidates:
                        continue
                    mrp_block = sorted(mrp_candidates, key=lambda x: x["y0"])[0]
                    price_match = re.search(r'(?:MRP|`)\D*([\d,]+(?:\.\d+)?)', mrp_block["text"], re.IGNORECASE)
                    if not price_match:
                        continue
                    price = price_match.group(1).replace(",", "").split(".")[0]

                    name_candidates = [
                        x for x in parsed_blocks
                        if x["col"] == col
                        and x["y1"] <= (sku_y + 2)
                        and (sku_y - x["y0"]) <= 220
                        and not is_meta(x["upper"])
                    ]
                    name_block = sorted(name_candidates, key=lambda x: x["y0"])[-1] if name_candidates else None
                    product_name = name_block["text"] if name_block else sku_code

                    detail_start_y = name_block["y1"] if name_block else max(sku_y - 120, 0)
                    detail_blocks = [
                        x for x in parsed_blocks
                        if x["col"] == col
                        and detail_start_y <= x["y0"] <= (mrp_block["y1"] + 2)
                        and x["upper"].startswith(("QTY:", "FORMAT:", "USAGE AREA:"))
                    ]
                    detail_lines = [x["text"] for x in sorted(detail_blocks, key=lambda x: x["y0"])]

                    assembled_lines = [product_name] + detail_lines + [f"SKU Code: {sku_code}", f"MRP: `{price}"]
                    assembled_text = "\n".join(assembled_lines)

                    cx = (sb["x0"] + sb["x1"]) / 2
                    cy = (sb["y0"] + mrp_block["y1"]) / 2
                    best_img_idx = -1
                    best_dist = float("inf")
                    for i_idx, ir in enumerate(img_records):
                        if ir["rect"] is None:
                            continue
                        img_rect = ir["rect"]
                        img_cx = (img_rect.x0 + img_rect.x1) / 2
                        img_cy = (img_rect.y0 + img_rect.y1) / 2
                        dx = abs(img_cx - cx)
                        dy = img_cy - cy
                        v_penalty = 0
                        if dy > 50:
                            v_penalty = 300
                        if dy < -400:
                            v_penalty = 200
                        dist = (dx**2 + dy**2) ** 0.5 + v_penalty
                        if dist < best_dist and dist < 800:
                            best_dist = dist
                            best_img_idx = i_idx
                    img_path = img_records[best_img_idx]["path"] if best_img_idx != -1 else ""

                    if current_category == "Cleaning Solutions":
                        inferred_category = "Cleaning Solutions"
                    else:
                        inferred_category = map_kohler_category(assembled_text) or current_category or "Cleaning Solutions"
                    page_items.append({
                        "text": assembled_text,
                        "name": product_name,
                        "price": price,
                        "page": page_num + 1,
                        "source": pdf_name,
                        "images": [img_path] if img_path else [],
                        "brand": brand,
                        "category": inferred_category
                    })

            # Fallback for Kohler table pages where model code and MRP are in separate lines.
            # Example: LIB/BRAZN pages with sequences like:
            #   K-702250IN-RH0-AF
            #   ...details...
            #   MRP ` 1,80,000.00
            code_line_re = re.compile(r'^\s*K\s*-\s*[A-Z0-9]+(?:-[A-Z0-9]+)*\s*$', re.IGNORECASE)
            existing_codes = set()
            for it in page_items:
                blob = f"{it.get('name', '')}\n{it.get('text', '')}"
                for m in kohler_code_re.findall(blob):
                    existing_codes.add(normalize_kohler_code(m))

            code_anchor_y = {}
            for b in blocks:
                if b[6] != 0:
                    continue
                x0, y0, x1, y1 = b[:4]
                raw_text = str(b[4]).strip()
                if not raw_text:
                    continue
                normalized = " ".join([ln.strip() for ln in raw_text.splitlines() if ln.strip()])
                for m in kohler_code_re.findall(normalized):
                    c = normalize_kohler_code(m)
                    if c not in code_anchor_y or y0 < code_anchor_y[c]:
                        code_anchor_y[c] = y0

            table_images = []
            for ir in img_records:
                rect = ir.get("rect")
                if rect is None:
                    continue
                table_images.append({
                    "path": ir["path"],
                    "cx": (rect.x0 + rect.x1) / 2,
                    "cy": (rect.y0 + rect.y1) / 2
                })

            def pick_table_image_for_code(code):
                y_anchor = code_anchor_y.get(code)
                if y_anchor is None or not table_images:
                    return ""
                best_path = ""
                best_score = float("inf")
                for ti in table_images:
                    # Prefer left-column thumbnails that align vertically with the code row.
                    x_penalty = 0 if ti["cx"] <= 180 else 260
                    score = abs(ti["cy"] - y_anchor) + x_penalty
                    if score < best_score:
                        best_score = score
                        best_path = ti["path"]
                return best_path

            text_lines = [ln.strip() for ln in page.get_text("text").splitlines() if ln.strip()]
            code_line_count = sum(1 for ln in text_lines if code_line_re.match(ln))

            if code_line_count >= 4:
                section_title = ""
                group_codes = []
                group_desc = []
                group_prices = []

                def flush_table_group():
                    nonlocal group_codes, group_desc, group_prices
                    if not group_codes:
                        return

                    desc_lines = [d for d in group_desc if d and "incl of all taxes" not in d.lower()]
                    title_candidates = [
                        d for d in desc_lines
                        if not re.search(r'^(width|depth|height|size)\b', d, re.IGNORECASE)
                    ]
                    shared_detail = [d for d in desc_lines if d not in title_candidates]

                    for i, raw_code in enumerate(group_codes):
                        code = normalize_kohler_code(raw_code)
                        if code in existing_codes:
                            continue

                        title = title_candidates[i] if i < len(title_candidates) else (title_candidates[0] if title_candidates else code)
                        price = group_prices[i] if i < len(group_prices) else (group_prices[0] if group_prices else "0")

                        assembled = [title, code]
                        if section_title:
                            assembled.append(section_title)
                        assembled.extend(shared_detail[:4])
                        if price and price != "0":
                            assembled.append(f"MRP ` {price}")

                        assembled_text = "\n".join(assembled)
                        inferred_category = map_kohler_category(f"{section_title} {title}") or current_category or "Shower Enclosures"
                        img_path = pick_table_image_for_code(code)
                        page_items.append({
                            "text": assembled_text,
                            "name": f"{title} ({code})",
                            "price": price,
                            "page": page_num + 1,
                            "source": pdf_name,
                            "images": [img_path] if img_path else [],
                            "brand": brand,
                            "category": inferred_category
                        })
                        existing_codes.add(code)

                    group_codes = []
                    group_desc = []
                    group_prices = []

                for ln in text_lines:
                    up = ln.upper()
                    if up.startswith("*AS PER SITE CONDITIONS"):
                        flush_table_group()
                        break

                    is_code_line = bool(code_line_re.match(ln))
                    mrp_match = re.search(r'MRP\s*`?\s*([\d,]+(?:\.\d+)?)', ln, re.IGNORECASE)
                    is_mrp_line = mrp_match is not None
                    is_meta_line = (
                        up.isdigit()
                        or up in {"MODEL", "CODE", "DESCRIPTION", "RUNNING LENGTH", "MRP", "SIZE", "LIB PVD PRICE LIST"}
                        or up.startswith("(INCL OF ALL TAXES)")
                        or up.startswith("BRAZN GLASS UPGRADE PRICE LIST")
                    )

                    # If a group already has prices and we hit a non-price/non-code line, close it.
                    if group_codes and group_prices and (not is_code_line) and (not is_mrp_line) and ("INCL OF ALL TAXES" not in up):
                        flush_table_group()

                    if is_meta_line:
                        continue

                    if is_code_line:
                        if group_codes and (group_desc or group_prices):
                            flush_table_group()
                        code = normalize_kohler_code(ln)
                        group_codes.append(code)
                        continue

                    if is_mrp_line:
                        if group_codes:
                            price = mrp_match.group(1).replace(",", "").split(".")[0]
                            group_prices.append(price)
                        continue

                    # Section / finish labels like "Brazn - AF", "Brazn - RGD", etc.
                    if not group_codes and re.search(r'\b-\s*[A-Z0-9]{2,5}\b', up):
                        section_title = ln
                        continue

                    if group_codes:
                        group_desc.append(ln)

                flush_table_group()

            content_list.extend(page_items)
            continue  # Skip Aquant extraction for this page

        # ── 2. Extract products using built-in block grouping (Aquant) ──────
        blocks = page.get_text("blocks")
        
        # Helper to check if block is a product code
        def is_product_code(text):
            t = text.strip()
            words = t.split()
            if not words: return False
            w = words[0]
            # Simple numeric code: 1918, 9244
            if w.isdigit() and 4 <= len(w) <= 7: return True
            # Alpha-dash-numeric: A-123, AB-1234
            if re.match(r'^[A-Z]{1,3}-\d+', w): return True
            # Numeric-dash-alpha: 1234-A
            if re.match(r'^\d{3,}-[A-Z]', w): return True
            # Code with space and letters: 1918 AG, 1845 W
            if len(words) > 1 and words[0].isdigit() and len(words[0]) >= 4 and len(words[1]) <= 3:
                return True
            return False

        DASHBOARD_CATS = [
            "STONE WASH BASINS", "ARTISTIC WASH BASINS IN UNIQUE MATERIALS", 
            "CERAMIC PEDESTAL WASH BASINS", "CERAMIC BASINS IN WHITE & SPECIAL FINISHES",
            "CERAMIC SANITARY WARE IN SPECIAL FINISHES", "LIMITED EDITION SANITARY WARE IN SPECIAL FINISHES",
            "CERAMIC BASINS IN SPECIAL FINISHES", "CERAMIC WASH BASINS",
            "INTELLIGENT SMART TOILET AQUANEXX SERIES", "TOILETS",
            "FLUSH TANKS/PLATES & URINAL SENSORS IN SPECIAL FINISHES",
            "PRESTIGE COLLECTION BASIN MIXERS", "FAUCETS & SHOWERING SYSTEMS IN SPECIAL FINISHES",
            "FAUCETS & SPOUTS IN SPECIAL FINISHES", "SHOWERING SYSTEMS IN SPECIAL FINISHES",
            "BODY JETS & BODY SHOWERS IN SPECIAL FINISHES", "HAND SHOWERS IN SPECIAL FINISHES",
            "BATH FITTINGS IN SPECIAL FINISHES", "FAUCETS IN SPECIAL FINISHES", 
            "ALLIED PRODUCTS IN SPECIAL FINISHES", "ACCESSORIES IN SPECIAL FINISHES", 
            "FAUCETS & SHOWERING SYSTEMS IN CHROME FINISH", "FAUCETS IN CHROME FINISH", 
            "DIVERTERS & SHOWERING SYSTEMS IN CHROME & SPECIAL FINISH",
            "CONCEALED CEILING MOUNTED SHOWERS IN CHROME FINISH", "SHOWERS IN CHROME FINISH",
            "BODY JETS & BODY SHOWERS IN CHROME FINISH", "HAND SHOWERS & HEAD SHOWERS IN CHROME FINISH",
            "ALLIED PRODUCTS IN CHROME FINISH", "SS SHOWER PANELS IN MATT FINISH",
            "KITCHEN FAUCETS IN SPECIAL & CHROME FINISH", "FLOOR DRAINS IN CHROME & SPECIAL FINISHES",
            "BATH COMPONENTS", "OUR PROMISE", "CARE INSTRUCTIONS"
        ]

        def is_header(text):
            t_clean = text.strip()
            # If it's short or has digits, it's rarely a major header
            if len(t_clean) < 4 or any(c.isdigit() for c in t_clean):
                return None
            
            t_up = t_clean.upper().replace('\n', ' ').strip()
            
            # 1. Manual aliases
            if "LIMITED EDITION" in t_up and "SANITARY" in t_up: return "LIMITED EDITION SANITARY WARE IN SPECIAL FINISHES"
            if "FLUSH TANKS" in t_up and "URINAL" in t_up: return "FLUSH TANKS/PLATES & URINAL SENSORS IN SPECIAL FINISHES"
            if "INTELLIGENT SMART TOILET" in t_up: return "INTELLIGENT SMART TOILET AQUANEXX SERIES"
            if "FAUCETS IN CHROME FINISH" in t_up: return "FAUCETS IN CHROME FINISH"
            
            # 2. Strict / Partial matches to known categories
            best_match = None
            best_len = 0
            for dc in DASHBOARD_CATS:
                if dc in t_up:
                    if len(dc) > best_len:
                        best_len = len(dc)
                        best_match = dc
            
            return best_match

        def is_price_line(text):
            return "MRP" in text or '`' in text or '₹' in text

        # dynamically detect columns
        page_width = page.rect.width
        col_dividers = [0]
        x_starts = sorted(set(round(b[0] / 50) * 50 for b in blocks if b[6] == 0))
        prev = x_starts[0] if x_starts else 0
        for x in x_starts[1:]:
            if x - prev > page_width * 0.20:
                col_dividers.append(x)
            prev = x
        col_dividers.append(page_width + 1)
        
        def get_col(x):
            for i in range(len(col_dividers) - 1):
                if col_dividers[i] <= x < col_dividers[i + 1]: return i
            return 0

        grouped_products = []
        for b in blocks:
            if b[6] != 0: continue
            
            x0, y0, x1, y1 = b[:4]
            text = b[4].strip().replace('\u0003', ' ')
            if len(text) < 5: continue
            
            h = is_header(text)
            if h and y0 < 25:
                current_category = h.upper()
                print(f"   [CAT] Page {page_num+1} Update Category: {current_category}")
                continue
                
            col = get_col(x0)
            
            attached = False
            for prod in reversed(grouped_products):
                if prod['col'] != col: continue
                vertical_gap = y0 - prod['y1']
                
                # If block starts with a code, only attach if gap is tiny (<10)
                # otherwise start new group.
                is_code = is_product_code(text)
                if is_code and prod['has_code'] and vertical_gap > 10:
                    continue
                    
                if 0 <= vertical_gap <= 80:
                    prod['text'] += "\n" + text
                    prod['y1'] = max(prod['y1'], y1)
                    # Expand horizontal bounds to include all text in group
                    prod['x0'] = min(prod['x0'], x0)
                    prod['x1'] = max(prod['x1'], x1)
                    prod['has_code'] = prod['has_code'] or is_code
                    attached = True
                    break
            
            if not attached:
                grouped_products.append({
                    'col': col,
                    'text': text,
                    'has_code': is_product_code(text),
                    'y0': y0,
                    'y1': y1,
                    'x0': x0,
                    'x1': x1
                })

        page_products = []
        last_mrp_per_col = {}
        
        for p in grouped_products:
            text = p['text'].strip()
            col = p['col']
            
            # Robust price extraction (handles spans across newlines/dashes)
            t_comp = re.sub(r'[\s/\-]+', '', text)
            pm = re.search(r'(?:MRP|`|₹)[:.]?`?([\d,]+)', t_comp, re.IGNORECASE)
            
            block_master_price = "0"
            if pm:
                block_master_price = pm.group(1).replace(",", "")
                last_mrp_per_col[col] = block_master_price
            else:
                block_master_price = last_mrp_per_col.get(col, "0")

            clean_lines = [l.strip() for l in text.split('\n') if l.strip()]
            
            # Split block into multiple sub-products if multiple codes present
            sub_prods = []
            current_sp = {"name": "", "text": "", "price": block_master_price}
            
            # Pre-process lines to split those containing multiple product codes internally
            split_lines = []
            for l in clean_lines:
                # If line has 'l' or '|' and multiple codes, split it
                # Logic: Find all occurrences of product-code-like patterns
                parts = re.split(r'\s+[l|I]\s+(?=\d{4}|[A-Z]{1,3}-\d+|\d{3,}-[A-Z])', l)
                split_lines.extend([p.strip() for p in parts if p.strip()])

            for l in split_lines:
                # If line is a new product code, start new sub-product
                if is_product_code(l) and not ('MRP' in l.upper()):
                    if current_sp["name"]:
                        sub_prods.append(current_sp)
                    
                    # Check for inline price for this specific code
                    lp_comp = re.sub(r'[\s/\-]+', '', l)
                    im = re.search(r'(?:MRP|`|₹)[:.]?`?([\d,]+)', lp_comp, re.IGNORECASE)
                    sp_price = im.group(1).replace(",", "") if im else block_master_price
                    
                    current_sp = {"name": l[:120], "text": l, "price": sp_price}
                else:
                    is_size_line = "Size" in l or re.match(r'^\d+(\s*x\s*\d+)+', l)
                    is_mrp_line = 'MRP' in l.upper()
                    
                    if not current_sp["name"] and not is_mrp_line:
                        current_sp["name"] = l[:120]
                    elif current_sp["name"] and len(current_sp["name"]) < 20 and not is_mrp_line and not is_size_line:
                        # Append the descriptive name if it's not too long yet
                        if l not in current_sp["name"]:
                            current_sp["name"] += " - " + l[:100]
                    
                    current_sp["text"] += "\n" + l
                    
                    # Update price if MRP mentions found in secondary lines
                    lp_comp = re.sub(r'[\s/\-]+', '', l)
                    im = re.search(r'(?:MRP|`|₹)[:.]?`?([\d,]{3,})', lp_comp, re.IGNORECASE)
                    if im:
                        current_sp["price"] = im.group(1).replace(",", "")
            
            if current_sp["name"]:
                sub_prods.append(current_sp)

            # Filter out noisy non-product groups (e.g. index pages, page numbers)
            if not p['has_code'] and not is_price_line(text) and len(text) < 100:
                continue

            cx = (p['x0'] + p['x1']) / 2
            cy = (p['y0'] + p['y1']) / 2
            
            for sp in sub_prods:
                # Basic name cleaning
                name = sp["name"]
                if name.replace(' ', '').isdigit(): continue # Skip solitary page numbers

                page_products.append({
                    "text": sp["text"],
                    "name": name,
                    "price": sp["price"],
                    "page": page_num + 1,
                    "source": pdf_name,
                    "cx": cx,
                    "cy": cy,
                    "images": [],
                    "brand": brand,
                    "category": current_category
                })

        # Image Matching
        available_images = list(img_records)
        used_image_paths = set()
        
        for p_data in page_products:
            best_img_idx = -1
            best_dist = float("inf")
            
            for i_idx, ir in enumerate(available_images):
                if ir["rect"] is None: continue
                img_path = ir["path"]
                if img_path in used_image_paths: continue
                
                img_rect = ir["rect"]
                img_cx = (img_rect.x0 + img_rect.x1) / 2
                img_cy = (img_rect.y0 + img_rect.y1) / 2
                
                dx = abs(img_cx - p_data["cx"])
                dy = img_cy - p_data["cy"]
                
                # Penalize images far below the product text
                v_penalty = 0
                if dy > 50: v_penalty = 300 
                if dy < -400: v_penalty = 200 # Too far above
                
                dist = (dx**2 + dy**2)**0.5 + v_penalty
                
                if dist < best_dist and dist < 700:
                    best_dist = dist
                    best_img_idx = i_idx

            if best_img_idx != -1:
                img_path = available_images[best_img_idx]["path"]
                p_data["images"] = [img_path]
                used_image_paths.add(img_path)

        for p in page_products:
            if "cx" in p: del p["cx"]
            if "cy" in p: del p["cy"]
            content_list.append(p)

    return content_list

    return content_list


def chunk_content(content_list):
    return content_list
