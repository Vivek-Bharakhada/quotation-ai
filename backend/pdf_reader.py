import fitz  # PyMuPDF
import os
import re
import hashlib
from collections import defaultdict

from PIL import Image, ImageChops, ImageOps

import cloud_storage

RESAMPLING = getattr(Image, "Resampling", Image)


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


PRICE_PATTERNS = (
    re.compile(r'(?:MRP(?:\s+Per\s+Unit)?|₹|`)\s*[:.]?\s*`?\s*([\d][\d,]*(?:\.\d+)?)', re.IGNORECASE),
    re.compile(r'`\s*([\d][\d,]*(?:\.\d+)?)', re.IGNORECASE),
    re.compile(r'^\s*([\d]{1,3}(?:,\d{2,3})+)\s*$', re.IGNORECASE),
)

AQUANT_FINISH_HINTS = (
    "ANTIQUE BRONZE",
    "BRUSHED GOLD",
    "BRUSHED ROSE GOLD",
    "CHROME",
    "GOLD",
    "GRAPHITE GREY",
    "MATT BLACK",
    "ROSE GOLD",
    "WALNUT COLOUR",
    "WHITE GLASS",
    "WHITE",
)

AQUANT_SKIP_PAGES = {1, 2, 3, 92, 93, 94, 95, 96}
PRODUCT_DETAIL_HINTS = (
    "ACCESSORY",
    "ANGLE",
    "BASIN",
    "BATH",
    "BODY",
    "BRASS",
    "CERAMIC",
    "CLICK",
    "COUPLING",
    "DIVERTER",
    "DRAIN",
    "FAUCET",
    "FITTING",
    "FLUSH",
    "FUNCTION",
    "HAND",
    "HEAD",
    "HEALTH",
    "HOOK",
    "JET",
    "KIT",
    "MIXER",
    "MOUNTED",
    "OUTLET",
    "PANEL",
    "PIPE",
    "PLAIN",
    "PLATE",
    "SEAT",
    "SHOWER",
    "SMART",
    "SPOUT",
    "STONE",
    "SYSTEM",
    "TABLE",
    "TANK",
    "TOILET",
    "VALVE",
    "WALL",
    "WASH",
)
LEADING_PRODUCT_CODE_RE = re.compile(r'^((?:[A-Z]{1,3}-\d[\d-]*|\d[\d-]*))(?:\s+([A-Z0-9+]{1,5}))?', re.IGNORECASE)
FINISH_CODE_LABELS = {
    "B": "Glossy Black",
    "BC": "Beige Caramel",
    "BG": "Brushed Gold",
    "BRG": "Brushed Rose Gold",
    "BSS": "Brushed Stainless Steel Finish",
    "CP": "Chrome",
    "GB": "Glossy Black",
    "GG": "Graphite Grey/Glossy Gold",
    "LG": "Lunar Grey",
    "MB": "Matt Black",
    "MG": "Matt Grey",
    "MI": "Matt Ivory",
    "MW": "Matt White/White",
    "OG": "Olive Green",
    "RB": "Royal Blue",
    "RG": "Rose Gold",
    "RGB": "Rose Gold/Matt Black",
    "RGW": "Rose Gold/Matt White",
    "RN": "Royal Navy",
    "SB": "Sky Blue",
    "SG": "Seafoam Green",
    "TCR": "Terracotta Red",
    "W": "White",
    "G": "Gold",
    # Plumber Finishes
    "CP": "Chrome Plated",
    "CB": "Chrome Black",
    "CGY": "Chrome Grey",
    "CW": "Chrome White",
    "BCK": "Matt Black",
    "WTE": "Matt White",
    "GRY": "Matt Grey",
    "BCG": "Black Champagne Gold",
    "BRG": "Black Rose Gold",
    "WCG": "White Champagne Gold",
    "WRG": "White Rose Gold",
    "CNG": "Champagne Gold",
    "RGD": "Rose Gold",
    "GM": "Gun Metal",
}

AQUANT_FINISH_IMAGE_VARIANT_ORDER = ("BRG", "GG", "RG", "BG", "MB", "CP", "MI", "MG", "TCR", "OG", "SB", "RB", "G", "SSF", "AB", "AC", "BC", "ORB", "AN", "SN")

AQUANT_SPECIAL_FINISH_IMAGE_ROW_PAGES = set(range(4, 54)) | set(range(68, 83)) | {59, 61, 91}
AQUANT_SPECIAL_FINISH_ROW_TOLERANCE = 5.0


IMAGE_GENERATION_VERSION = "clip_v3_hd"
IMAGE_CANVAS_SIZE = 720
IMAGE_INNER_BOX = 620
MIN_PRODUCT_IMAGE_SHORT_SIDE = 60
MAX_PRODUCT_IMAGE_ASPECT_RATIO = 6.0
SUSPICIOUS_SHARED_IMAGE_ITEM_LIMIT = 12
SUSPICIOUS_SHARED_IMAGE_FAMILY_LIMIT = 8


AQUANT_MANUAL_FAMILY_OVERRIDES = {
    (40, "1313"): {"generic_name": "Ceiling Mounted Brass Basin Tap Mouth Operated", "cp_price": "23950", "variant_price": "35500"},
    (40, "1314"): {"generic_name": "Brass Extension Pipe", "cp_price": "4000", "variant_price": "5000"},
    (40, "1424"): {"generic_name": "Ceiling Mounted Brass Basin Spout", "cp_price": "23950", "variant_price": "35500"},
    (40, "1424-200"): {"generic_name": "200 mm Brass Extension Pipe", "cp_price": "2500", "variant_price": "3300"},
    (40, "1424-500"): {"generic_name": "500 mm Brass Extension Pipe", "cp_price": "5500", "variant_price": "7700"},
    (79, "1021"): {
        "generic_name": "Ceramic Pop-Up Waste Coupling",
        "variant_prices": {
            "BC": "2750",
            "GB": "2750",
            "LG": "2750",
            "MB": "2750",
            "MG": "2750",
            "RN": "2750",
            "SG": "2750",
            "W": "2500",
        },
    },
}

AQUANT_EXACT_ITEM_OVERRIDES = {
    (40, "1424-200", ""): "1424-200 - 200 mm Brass Extension Pipe",
}

AQUANT_PAGE_CODE_OVERRIDES = {
    58: {
        "60080 TL": {"generic_name": "Line-Design Shower Channel Drain", "detail": "Without Base (304 SS)", "price": "2850", "image_slot": "TL"},
        "750080 TL": {"generic_name": "Line-Design Shower Channel Drain", "detail": "Without Base (304 SS)", "price": "3575", "image_slot": "TL"},
        "90080 TL": {"generic_name": "Line-Design Shower Channel Drain", "detail": "Without Base (304 SS)", "price": "5500", "image_slot": "TL"},
        "120080 TL": {"generic_name": "Line-Design Shower Channel Drain", "detail": "Without Base (304 SS)", "price": "6700", "image_slot": "TL"},
        "60080 TI": {"generic_name": "Tile-Insert Shower Channel Drain", "detail": "Without Base (304 SS)", "price": "3400", "image_slot": "TI"},
        "750080 TI": {"generic_name": "Tile-Insert Shower Channel Drain", "detail": "Without Base (304 SS)", "price": "4250", "image_slot": "TI"},
        "90080 TI": {"generic_name": "Tile-Insert Shower Channel Drain", "detail": "Without Base (304 SS)", "price": "6100", "image_slot": "TI"},
        "120080 TI": {"generic_name": "Tile-Insert Shower Channel Drain", "detail": "Without Base (304 SS)", "price": "7150", "image_slot": "TI"},
        "60080 BS": {"generic_name": "Shower Channel Base (304 SS)", "price": "4400", "image_slot": "BS"},
        "750080 BS": {"generic_name": "Shower Channel Base (304 SS)", "price": "5000", "image_slot": "BS"},
        "90080 BS": {"generic_name": "Shower Channel Base (304 SS)", "price": "6100", "image_slot": "BS"},
        "120080 BS": {"generic_name": "Shower Channel Base (304 SS)", "price": "11000", "image_slot": "BS"},
        "60080 BS CH": {"generic_name": "Shower Channel Base (304 SS)", "price": "4400", "image_slot": "BS CH"},
        "750080 BS CH": {"generic_name": "Shower Channel Base (304 SS)", "price": "5000", "image_slot": "BS CH"},
        "90080 BS CH": {"generic_name": "Shower Channel Base (304 SS)", "price": "6100", "image_slot": "BS CH"},
        "120080 BS CH": {"generic_name": "Shower Channel Base (304 SS)", "price": "11000", "image_slot": "BS CH"},
    },
}

AQUANT_PAGE_IMAGE_ANCHORS = {
    58: {
        "TL": (82.0, 109.0),
        "TI": (226.0, 103.0),
        "BS": (369.0, 104.0),
        "BS CH": (512.0, 104.0),
    },
}


def extract_price_value(text):
    cleaned = clean_text(text or "")
    for pattern in PRICE_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            return match.group(1).replace(",", "").split(".")[0]
    return None


def _image_short_side(width, height):
    return min(int(width or 0), int(height or 0))


def _image_aspect_ratio(width, height):
    short_side = max(1, _image_short_side(width, height))
    return max(int(width or 0), int(height or 0)) / short_side


def _white_ratio(image):
    sample = image.convert("RGB").resize((64, 64))
    total = 64 * 64
    bright = 0
    for r, g, b in sample.getdata():
        if r >= 243 and g >= 243 and b >= 243:
            bright += 1
    return bright / total


def _trim_possible_caption_band(image):
    width, height = image.size
    if width < 80 or height < 120:
        return image

    candidates = (0.92, 0.88, 0.84)
    for cutoff_ratio in candidates:
        cutoff = int(height * cutoff_ratio)
        if cutoff <= int(height * 0.6):
            continue

        bottom_band = image.crop((0, cutoff, width, height))
        upper_band = image.crop((0, max(0, cutoff - max(24, height // 8)), width, cutoff))
        bottom_white = _white_ratio(bottom_band)
        upper_white = _white_ratio(upper_band) if upper_band.size[1] > 0 else 0.0

        if bottom_white >= 0.86 and bottom_white >= upper_white + 0.12:
            return image.crop((0, 0, width, cutoff))

    return image


def _trim_white_border(image):
    rgb_image = image.convert("RGB")
    bg = Image.new("RGB", rgb_image.size, "white")
    diff = ImageChops.difference(rgb_image, bg)
    bbox = diff.getbbox()
    if not bbox:
        return rgb_image

    left, top, right, bottom = bbox
    margin_x = max(6, int((right - left) * 0.04))
    margin_y = max(6, int((bottom - top) * 0.04))
    return rgb_image.crop((
        max(0, left - margin_x),
        max(0, top - margin_y),
        min(rgb_image.width, right + margin_x),
        min(rgb_image.height, bottom + margin_y),
    ))


def _render_hd_product_image(image_path):
    with Image.open(image_path) as image:
        rgb_image = image.convert("RGB")
        rgb_image = _trim_possible_caption_band(rgb_image)
        rgb_image = _trim_white_border(rgb_image)
        content_width, content_height = rgb_image.size

        canvas = Image.new("RGB", (IMAGE_CANVAS_SIZE, IMAGE_CANVAS_SIZE), "white")
        fitted = ImageOps.contain(rgb_image, (IMAGE_INNER_BOX, IMAGE_INNER_BOX), method=RESAMPLING.LANCZOS)
        offset_x = (IMAGE_CANVAS_SIZE - fitted.width) // 2
        offset_y = (IMAGE_CANVAS_SIZE - fitted.height) // 2
        canvas.paste(fitted, (offset_x, offset_y))
        canvas.save(image_path, format="JPEG", quality=92, optimize=True)

    return {
        "content_width": content_width,
        "content_height": content_height,
        "short_side": _image_short_side(content_width, content_height),
        "aspect_ratio": _image_aspect_ratio(content_width, content_height),
    }


def _is_reasonable_product_image(image_meta):
    if not image_meta:
        return False
    if image_meta.get("short_side", 0) < MIN_PRODUCT_IMAGE_SHORT_SIDE:
        return False
    if image_meta.get("aspect_ratio", 0.0) > MAX_PRODUCT_IMAGE_ASPECT_RATIO:
        return False
    return True


def _prune_suspicious_page_images(page_products, image_records):
    if not page_products or not image_records:
        return

    records_by_path = {
        record["path"]: record for record in image_records
        if record.get("path")
    }
    path_usage = defaultdict(int)
    family_usage = defaultdict(set)

    for item in page_products:
        family_key = extract_product_family_key(item.get("name", "")) or clean_text(item.get("name", ""))
        for image_path in item.get("images") or []:
            path_usage[image_path] += 1
            if family_key:
                family_usage[image_path].add(family_key)

    blocked_paths = set()
    for image_path, count in path_usage.items():
        record = records_by_path.get(image_path, {})
        image_meta = record.get("image_meta") or {}
        if not _is_reasonable_product_image(image_meta):
            blocked_paths.add(image_path)
            continue

        if (
            count > SUSPICIOUS_SHARED_IMAGE_ITEM_LIMIT
            and len(family_usage.get(image_path, set())) > SUSPICIOUS_SHARED_IMAGE_FAMILY_LIMIT
        ):
            blocked_paths.add(image_path)

    if not blocked_paths:
        return

    for item in page_products:
        if not item.get("images"):
            continue
        item["images"] = [
            image_path for image_path in item.get("images", [])
            if image_path not in blocked_paths
        ]


def _score_catalog_image_match(item, image_record, page_half):
    rect = image_record.get("rect")
    if rect is None or not image_record.get("path"):
        return None

    p_cx = item.get("cx") or 0
    p_cy = item.get("cy") or 0
    p_col = 0 if p_cx < page_half else 1

    img_cx = (rect.x0 + rect.x1) / 2
    img_cy = (rect.y0 + rect.y1) / 2
    i_col = 0 if img_cx < page_half else 1

    dx = abs(img_cx - p_cx)
    dy = img_cy - p_cy
    col_penalty = 0 if p_col == i_col else 400
    v_penalty = 0
    if dy > 50:
        v_penalty = 300
    if dy < -450:
        v_penalty = 200

    distance = (dx ** 2 + dy ** 2) ** 0.5 + v_penalty + col_penalty
    if distance >= 750:
        return None

    return distance


def _assign_catalog_images_globally(page_products, available_images, page_half):
    candidate_pairs = []
    for product_index, item in enumerate(page_products):
        if item.get("images"):
            continue
        for image_record in available_images:
            score = _score_catalog_image_match(item, image_record, page_half)
            if score is None:
                continue
            rect = image_record["rect"]
            candidate_pairs.append(
                (
                    score,
                    abs(((rect.y0 + rect.y1) / 2) - (item.get("cy") or 0)),
                    abs(((rect.x0 + rect.x1) / 2) - (item.get("cx") or 0)),
                    product_index,
                    image_record["path"],
                )
            )

    assigned_products = set()
    used_image_paths = set()

    for _, _, _, product_index, image_path in sorted(candidate_pairs):
        if product_index in assigned_products or image_path in used_image_paths:
            continue
        page_products[product_index]["images"] = [image_path]
        assigned_products.add(product_index)
        used_image_paths.add(image_path)


def strip_price_markup(text):
    cleaned = clean_text(text or "")
    cleaned = re.sub(r'\bMRP\b.*$', '', cleaned, flags=re.IGNORECASE).strip(" -:\t")
    return cleaned.strip()


def is_aquant_finish_line(text):
    upper = clean_text(text or "").upper()
    if not upper:
        return False
    if len(upper) <= 48 and any(token in upper for token in AQUANT_FINISH_HINTS):
        return True
    if upper.startswith("(") and upper.endswith(")") and any(token in upper for token in AQUANT_FINISH_HINTS):
        return True
    return False


def split_variant_display_name(name):
    cleaned = clean_text(name or "")
    if " - " not in cleaned:
        return cleaned, ""
    head, tail = cleaned.split(" - ", 1)
    return head.strip(), tail.strip()


def normalize_label(text):
    return re.sub(r'[^A-Z0-9]+', '', clean_text(text or "").upper())


def extract_product_code_parts(text):
    cleaned = clean_text(text or "")
    match = LEADING_PRODUCT_CODE_RE.match(cleaned)
    if not match:
        return "", ""
    base_code = (match.group(1) or "").upper()
    variant_token = (match.group(2) or "").upper()
    if variant_token in {"MRP", "SIZE"}:
        variant_token = ""
    return base_code, variant_token


def extract_product_family_key(text):
    return extract_product_code_parts(text)[0]


def extract_variant_token(text):
    return extract_product_code_parts(text)[1]


def split_aquant_segments(text):
    cleaned = clean_text(text or "")
    if not cleaned:
        return []

    # First, split by obvious separators
    initial_tokens = re.split(r'\|', cleaned)
    
    # Then for each token, check if it contains multiple product codes clumped together
    # Rule: Split before a 4-digit code if it's preceded by letters or more than 2 spaces
    tokens = []
    for tok in initial_tokens:
        sub_tokens = re.split(r'(?=\b\d{4}[A-Z]{1,4}\b|\b\d{4}\s+[A-Z]{1,4}\b)', tok)
        tokens.extend([clean_text(st) for st in sub_tokens if clean_text(st)])

    if not tokens:
        return []
    if len(tokens) <= 1:
        return [cleaned]

    segments = []
    current = ""
    for token in tokens:
        token_without_price = strip_price_markup(token)
        starts_code = bool(token_without_price and extract_product_family_key(token_without_price))
        starts_price = bool(re.search(r'\bMRP\b|^`|^₹', token, re.IGNORECASE))

        if starts_code:
            if current:
                segments.append(current)
            current = token
            continue

        if starts_price:
            current_has_code = bool(extract_product_family_key(current))
            current_is_price_only = bool(re.search(r'\bMRP\b|^`|^₹', current, re.IGNORECASE)) and not current_has_code
            if current and current_is_price_only:
                segments.append(current)
                current = token
            else:
                current = f"{current} | {token}" if current else token
            continue

        current = f"{current} | {token}" if current else token

    if current:
        segments.append(current)
    return segments


def extract_price_label(text):
    cleaned = clean_text(text or "")
    if not cleaned:
        return ""

    patterns = (
        re.compile(r'(?:MRP|₹|`)\s*[:.]?\s*`?\s*[\d][\d,]*(?:\.\d+)?\s*(?:/-)?\s*(.*)$', re.IGNORECASE),
        re.compile(r'^\s*[\d]{1,3}(?:,\d{2,3})+\s*(?:/-)?\s*(.*)$', re.IGNORECASE),
    )
    for pattern in patterns:
        match = pattern.search(cleaned)
        if match:
            return clean_text(match.group(1) or "").strip(" -|")
    return ""


def is_variant_stub_text(text):
    cleaned = clean_text(text or "")
    upper = cleaned.upper()
    if not upper:
        return True
    if is_aquant_finish_line(cleaned):
        return True
    return len(upper) <= 40 and not any(keyword in upper for keyword in PRODUCT_DETAIL_HINTS)


def extract_item_finish_label(item):
    variant_token = extract_variant_token(item.get("name", ""))
    if variant_token in FINISH_CODE_LABELS:
        return FINISH_CODE_LABELS[variant_token]

    for raw in (item.get("name", ""), item.get("text", "")):
        lines = [clean_text(line) for line in str(raw or "").split("\n") if clean_text(line)]
        for line in reversed(lines):
            if extract_product_family_key(line):
                continue
            if "MRP" in line.upper() or "SIZE" in line.upper():
                continue
            if len(line) <= 48:
                return line

        dash_parts = [part.strip() for part in clean_text(raw).split(" - ") if part.strip()]
        if len(dash_parts) >= 2:
            candidate = dash_parts[-1]
            if candidate and len(candidate) <= 48 and "MRP" not in candidate.upper():
                return candidate
    return ""


def strip_finish_phrase(text, finish_label=""):
    cleaned = clean_text(text or "")
    finish_label = clean_text(finish_label or "")
    if not cleaned or not finish_label:
        return cleaned

    finish_key = normalize_label(finish_label)
    if not finish_key:
        return cleaned

    if cleaned.upper().startswith(finish_label.upper()):
        cleaned = cleaned[len(finish_label):].strip(" -/+")
    if cleaned.upper().endswith(finish_label.upper()):
        cleaned = cleaned[:-len(finish_label)].strip(" -/+")

    kept_parts = []
    for part in [segment.strip() for segment in cleaned.split(" - ") if segment.strip()]:
        part_key = normalize_label(part)
        if part_key and (part_key == finish_key or part_key in finish_key or finish_key in part_key):
            continue
        kept_parts.append(part)

    return " - ".join(kept_parts).strip(" -/+")


def extract_inline_product_description(text, finish_label=""):
    cleaned = clean_text(text or "")
    if not cleaned:
        return ""

    cleaned = re.split(r'\b(?:SIZE|MRP)\b', cleaned, maxsplit=1, flags=re.IGNORECASE)[0]
    cleaned = re.sub(
        r'^((?:[A-Z]{1,3}-\d[\d-]*|\d[\d-]*))(?:\s+[A-Z0-9+]{1,5})?\s*[-:]?\s*',
        '',
        cleaned,
        count=1,
        flags=re.IGNORECASE,
    )
    cleaned = strip_finish_phrase(cleaned, finish_label)
    return cleaned.strip(" -|:/")


def extract_generic_description(item):
    name = clean_text(item.get("name", ""))
    finish_label = extract_item_finish_label(item)
    candidates = []

    inline_name = extract_inline_product_description(name, finish_label)
    if inline_name and not is_variant_stub_text(inline_name):
        candidates.append(inline_name)
    elif not extract_product_family_key(name) and name and not is_variant_stub_text(name):
        candidates.append(name)

    if " - " in name:
        _, tail = split_variant_display_name(name)
        tail_parts = [part.strip() for part in tail.split(" - ") if part.strip()]
        while tail_parts and is_variant_stub_text(tail_parts[-1]):
            tail_parts.pop()
        if tail_parts:
            tail_candidate = strip_finish_phrase(" - ".join(tail_parts), finish_label)
            if tail_candidate and not is_variant_stub_text(tail_candidate):
                candidates.append(tail_candidate)

    for line in (clean_text(part) for part in str(item.get("text", "")).split("\n")):
        if not line:
            continue
        inline_candidate = extract_inline_product_description(line, finish_label)
        if (
            inline_candidate
            and any(keyword in inline_candidate.upper() for keyword in PRODUCT_DETAIL_HINTS)
            and not is_variant_stub_text(inline_candidate)
        ):
            candidates.append(inline_candidate)

        if extract_product_family_key(line):
            continue
        if "MRP" in line.upper():
            continue
        if "SIZE" in line.upper() or re.match(r'^\d+(\s*x\s*\d+)+', line, re.IGNORECASE):
            continue
        line = strip_finish_phrase(line, finish_label)
        if not line or is_variant_stub_text(line):
            continue
        candidates.append(line)

    seen = set()
    merged = []
    for candidate in candidates:
        key = normalize_label(candidate)
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(candidate)
    return merged[0] if merged else ""


def merge_variant_details(item, generic_desc="", finish_label=""):
    generic_desc = clean_text(generic_desc or "")
    finish_label = clean_text(finish_label or extract_item_finish_label(item))
    item_name = clean_text(item.get("name", ""))
    if normalize_label(finish_label).isdigit():
        finish_label = ""
    if generic_desc:
        generic_desc = strip_finish_phrase(generic_desc, finish_label) or generic_desc

    generic_key = normalize_label(generic_desc)
    finish_key = normalize_label(finish_label)
    if generic_key and finish_key and (finish_key in generic_key or generic_key in finish_key):
        finish_label = ""
        finish_key = ""

    code_part = item_name
    if " - " in item_name:
        code_part, _ = split_variant_display_name(item_name)

    name_parts = [code_part] if code_part else []
    if generic_desc and normalize_label(generic_desc) not in normalize_label(code_part):
        name_parts.append(generic_desc)
    if finish_label and normalize_label(finish_label) != normalize_label(generic_desc):
        name_parts.append(finish_label)

    new_name = " - ".join(part for part in name_parts if part)
    if new_name:
        item["name"] = new_name

    existing_lines = [clean_text(line) for line in str(item.get("text", "")).split("\n") if clean_text(line)]
    merged_lines = [item["name"]]
    if generic_desc and generic_desc not in merged_lines:
        merged_lines.append(generic_desc)
    if finish_label and finish_label not in merged_lines:
        merged_lines.append(finish_label)

    for line in existing_lines:
        if normalize_label(line) == normalize_label(item["name"]):
            continue
        if "MRP" in line.upper():
            continue
        if line in merged_lines:
            continue
        merged_lines.append(line)

    if str(item.get("price") or "0") not in {"", "0"}:
        merged_lines.append(f"MRP : ` {item['price']}/-")

    item["text"] = "\n".join(merged_lines)


def normalize_aquant_item(item):
    variant_token = extract_variant_token(item.get("name", ""))
    generic_desc = extract_generic_description(item)
    finish_label = clean_text(extract_item_finish_label(item))

    if variant_token == "":
        raw_candidates = []
        for line in (clean_text(part) for part in str(item.get("text", "")).split("\n")):
            if not line:
                continue
            if extract_product_family_key(line):
                continue
            if "MRP" in line.upper() or "SIZE" in line.upper():
                continue
            candidate = strip_finish_phrase(line, finish_label)
            if (
                candidate
                and any(keyword in candidate.upper() for keyword in PRODUCT_DETAIL_HINTS)
                and not is_variant_stub_text(candidate)
            ):
                raw_candidates.append(candidate)

        if raw_candidates:
            generic_desc = min(raw_candidates, key=len)

    if variant_token == "" and finish_label and any(keyword in finish_label.upper() for keyword in PRODUCT_DETAIL_HINTS):
        finish_label = ""

    if variant_token in FINISH_CODE_LABELS and not finish_label:
        finish_label = FINISH_CODE_LABELS[variant_token]

    if generic_desc or finish_label:
        merge_variant_details(item, generic_desc, finish_label)


def resolve_aquant_page_image_slots(page_number, img_records):
    anchors = AQUANT_PAGE_IMAGE_ANCHORS.get(page_number, {})
    if not anchors:
        return {}

    slot_paths = {}
    for slot_name, (anchor_x, anchor_y) in anchors.items():
        best_path = ""
        best_score = float("inf")
        for ir in img_records:
            rect = ir.get("rect")
            if rect is None or not ir.get("path"):
                continue
            cx = (rect.x0 + rect.x1) / 2
            cy = (rect.y0 + rect.y1) / 2
            score = ((cx - anchor_x) ** 2 + (cy - anchor_y) ** 2) ** 0.5
            if score < best_score:
                best_score = score
                best_path = ir["path"]
        if best_path and best_score < 140:
            slot_paths[slot_name] = best_path
    return slot_paths


def apply_aquant_page_code_overrides(page_num, page_products, img_records):
    page_number = page_num + 1
    overrides = AQUANT_PAGE_CODE_OVERRIDES.get(page_number)
    if not overrides:
        return

    slot_paths = resolve_aquant_page_image_slots(page_number, img_records)
    ordered_codes = sorted(overrides.keys(), key=len, reverse=True)

    for item in page_products:
        item_name = clean_text(item.get("name", "")).upper()
        matched_code = next((code for code in ordered_codes if item_name.startswith(code)), "")
        if not matched_code:
            continue

        override = overrides[matched_code]
        name_parts = [matched_code, override["generic_name"]]
        if override.get("detail"):
            name_parts.append(override["detail"])

        item["name"] = " - ".join(part for part in name_parts if part)
        item["price"] = override["price"]

        text_lines = [item["name"], override["generic_name"]]
        if override.get("detail"):
            text_lines.append(override["detail"])
        text_lines.append(matched_code)
        text_lines.append(f"MRP : ` {override['price']}/-")
        item["text"] = "\n".join(line for line in text_lines if line)

        slot_path = slot_paths.get(override.get("image_slot", ""))
        if slot_path:
            item["images"] = [slot_path]


def build_aquant_image_rows(img_records, y_tolerance=AQUANT_SPECIAL_FINISH_ROW_TOLERANCE):
    image_points = []
    for ir in img_records:
        rect = ir.get("rect")
        path = ir.get("path")
        if rect is None or not path:
            continue
        image_points.append(
            {
                "path": path,
                "cx": (rect.x0 + rect.x1) / 2,
                "cy": (rect.y0 + rect.y1) / 2,
            }
        )

    image_points.sort(key=lambda point: (point["cy"], point["cx"]))
    rows = []
    for point in image_points:
        if rows and abs(rows[-1]["cy"] - point["cy"]) <= y_tolerance:
            rows[-1]["images"].append(point)
            rows[-1]["cy"] = sum(img["cy"] for img in rows[-1]["images"]) / len(rows[-1]["images"])
        else:
            rows.append({"cy": point["cy"], "images": [point]})

    for row in rows:
        row["images"].sort(key=lambda point: point["cx"])

    return rows


def apply_aquant_special_finish_image_rows(page_num, page_products, img_records):
    # This function resolves image mapping for "Special Finish" pages in Aquant PDF
    # where multiple colors (Matt Black, Gold, etc.) are shown in a grid or row.
    page_number = page_num + 1
    
    # Auto-detect special pages by checking the category/header
    is_special_page = page_number in AQUANT_SPECIAL_FINISH_IMAGE_ROW_PAGES
    if not is_special_page:
        sample_cats = [it.get("category", "").upper() for it in page_products[:15]]
        if any("SPECIAL FINISH" in c or "UNIQUE MATERIAL" in c or "PVD FINISH" in c for c in sample_cats):
            is_special_page = True
            
    if not is_special_page:
        return

    # Group products by their base family (e.g., all 1505 variants together)
    family_buckets = {}
    for item in page_products:
        family_key = extract_product_family_key(item.get("name", ""))
        if family_key:
            family_buckets.setdefault(family_key, []).append(item)

    for family_key, bucket_items in family_buckets.items():
        # Visual Alignment Strategy:
        # Instead of guessing rows, we look for images that are vertically aligned with the items.
        # This handles grids (1505) and long rows perfectly.
        
        family_cy_min = min(item.get("cy", 0) for item in bucket_items)
        family_cy_max = max(item.get("cy", 0) for item in bucket_items)
        
        # Look for images within 550pt above or 150pt below the family y-range
        nearby_images = [
            img for img in img_records
            if (family_cy_min - 550) <= (img["rect"].y1 + img["rect"].y0)/2 <= (family_cy_max + 150)
        ]
        
        if not nearby_images:
            continue
            
        for item in bucket_items:
            # Skip if already has image (manual overrides)
            if item.get("images"): continue
            
            p_cx = item.get("cx", 0)
            p_cy = item.get("cy", 0)
            
            # Find best nearby image based on horizontal alignment
            best_img = None
            best_score = float("inf")
            
            for img in nearby_images:
                img_rect = img["rect"]
                img_cx = (img_rect.x0 + img_rect.x1) / 2
                img_cy = (img_rect.y0 + img_rect.y1) / 2
                
                dx = abs(img_cx - p_cx)
                dy = img_cy - p_cy # positive if image is below, negative if image is above
                
                # We prefer images directly ABOVE (-dy) or slightly below (+dy)
                v_penalty = 0
                if dy > 50: v_penalty = 200 # Penalize images below label
                if dy < -450: v_penalty = 150 # Penalize very far images
                
                # Weight horizontal alignment VERY heavily (6.0x) for grid pages
                score = (dx * 6.0) + abs(dy) + v_penalty
                
                if score < best_score:
                    best_score = score
                    best_img = img
            
            if best_img and best_score < 750:
                item["images"] = [best_img["path"]]


def extract_content(pdf_path, max_pages=None):
    doc = fitz.open(pdf_path)
    content_list = []

    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_dir = os.path.join(base_dir, "static", "images")
    os.makedirs(image_dir, exist_ok=True)

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    pdf_prefix_seed = f"{pdf_name}|{os.path.getsize(pdf_path)}|{int(os.path.getmtime(pdf_path))}|{IMAGE_GENERATION_VERSION}"
    pdf_prefix_hash = hashlib.md5(pdf_prefix_seed.encode("utf-8")).hexdigest()[:10]
    pdf_prefix_base = re.sub(r'[^a-zA-Z0-9_]', '_', pdf_name)[:16]
    pdf_prefix = f"{pdf_prefix_base}_{pdf_prefix_hash}"

    num_pages = len(doc)
    if max_pages: num_pages = min(num_pages, max_pages)

    current_category = None
    brand = "Aquant" if "aquant" in pdf_name.lower() else "Kohler" if "kohler" in pdf_name.lower() else "Plumber" if "plumber" in pdf_name.lower() else "Generic"

    for page_num in range(num_pages):
        page = doc[page_num]

        # ── 1. Extract images with their bounding boxes ──────────────────
        img_records = []
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            rects = page.get_image_rects(xref)
            rect = rects[0] if rects else None
            if rect is None:
                continue

            width = img[2]
            height = img[3]
            display_width = rect.width
            display_height = rect.height
            pixel_area = width * height
            display_area = display_width * display_height
            if (
                max(width, height) < 20
                and max(display_width, display_height) < 18
            ) or (
                pixel_area < 1200
                and display_area < 250
            ):
                continue

            try:
                img_filename = f"{pdf_prefix}_p{page_num}_i{img_index}.jpg"
                img_path = os.path.join(image_dir, img_filename)
                image_meta = None
                if not os.path.exists(img_path):
                    clip_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1)
                    zoom = 3.2 if max(display_width, display_height) < 180 else 2.6
                    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip_rect, alpha=False)
                    pix.save(img_path)
                    pix = None
                    image_meta = _render_hd_product_image(img_path)
                else:
                    image_meta = _render_hd_product_image(img_path)

                public_path = f"/static/images/{img_filename}"
                if cloud_storage.is_enabled():
                    try:
                        public_path = cloud_storage.upload_file(
                            cloud_storage.PRODUCT_IMAGES_BUCKET,
                            f"catalog/{img_filename}",
                            img_path,
                            "image/jpeg",
                        )
                    except Exception:
                        public_path = f"/static/images/{img_filename}"

                img_records.append({
                    "path": public_path,
                    "rect": rect,
                    "image_meta": image_meta or {},
                })
            except Exception:
                continue

        # ── 1.2. Fallback for inline images (e.g. pg 53 ceiling showers) ─────
        try:
            d = page.get_text("dict")
            for i, b in enumerate(d.get("blocks", [])):
                if b.get("type") == 1: # Image block
                    rect = fitz.Rect(b["bbox"])
                    # Check for overlap with existing images to avoid duplicates
                    is_duplicate = False
                    for existing in img_records:
                        if rect.intersects(existing["rect"]) and rect.intersect(existing["rect"]).area > rect.area * 0.8:
                            is_duplicate = True
                            break
                    if is_duplicate:
                        continue
                        
                    img_filename = f"{pdf_prefix}_p{page_num}_block{i}.jpg"
                    img_path = os.path.join(image_dir, img_filename)
                    image_meta = None
                    if not os.path.exists(img_path):
                        zoom = 2.8
                        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=rect, alpha=False)
                        pix.save(img_path)
                        pix = None
                        image_meta = _render_hd_product_image(img_path)
                    else:
                        image_meta = _render_hd_product_image(img_path)
                    public_path = f"/static/images/{img_filename}"
                    if cloud_storage.is_enabled():
                        try:
                            public_path = cloud_storage.upload_file(
                                cloud_storage.PRODUCT_IMAGES_BUCKET,
                                f"catalog/{img_filename}",
                                img_path,
                                "image/jpeg",
                            )
                        except Exception:
                            public_path = f"/static/images/{img_filename}"

                    img_records.append({
                        "path": public_path,
                        "rect": rect,
                        "image_meta": image_meta or {},
                    })
        except Exception:
            pass
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

        def map_plumber_category(text):
            t = text.upper().strip()
            if "EXOTICA" in t:
                return t.replace("EXOTICA", "").strip().title()
            if "SHOWERS" in t: return "Showers"
            if "ACCESSORIES" in t: return "Accessories"
            if "THERMOSTATIC" in t: return "Thermostatic Mixers"
            if "UNIVERSAL ITEMS" in t: return "Universal Items"
            if "FAUCETS COLLECTION" in t: return "Faucets"
            return None

        # Kohler model codes are consistently hyphenated (e.g. K-1063956, K-24149IN-F-BN).
        kohler_code_re = re.compile(r'\bK\s*-\s*[A-Z0-9]+(?:-[A-Z0-9]+)*\b', re.IGNORECASE)
        # Plumber codes like DUN-1101, U-0901, BZA-1904C
        plumber_code_re = re.compile(r'\b[A-Z]{1,4}\s*-\s*[A-Z0-9]+(?:-[A-Z0-9]+)*\b', re.IGNORECASE)

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
                        
                        code = normalize_kohler_code(code_match.group(0))
                        
                        # Clean up text lines for description
                        raw_lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
                        desc_lines = [ln for ln in raw_lines if code.upper() not in ln.upper() and 'MRP' not in ln.upper() and '(INCL' not in ln.upper()]
                        primary_desc = desc_lines[0] if desc_lines else ""
                        
                        # Build a proper display name: [CODE] - [DESCRIPTION]
                        if last_name:
                            prod_name = f"{code} - {last_name} {primary_desc}".strip(" -")
                        else:
                            prod_name = f"{code} - {primary_desc}".strip(" -")
                            
                        if current_category == "Cleaning Solutions":
                            inferred_category = "Cleaning Solutions"
                        else:
                            inferred_category = map_kohler_category(f"{last_name} {text}") or current_category or "Uncategorized"
                            
                        # Clean up the text block for display
                        display_lines = [prod_name]
                        if len(desc_lines) > 1:
                            display_lines.extend(desc_lines[1:])
                        display_lines.append(f"MRP : ` {price}/-")
                        
                        page_items.append({
                            "text": "\n".join(display_lines),
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

        if brand == "Plumber":
            blocks = page.get_text("blocks")
            blocks.sort(key=lambda b: (b[1], b[0]))
            
            # ── Finish Header Detection ──
            finish_labels = ["CP"] 
            potential_header_texts = []
            for b in blocks:
                if b[6] != 0: continue
                if b[1] < 280: # Headers are usually at the top
                    potential_header_texts.append(b[4].strip())
            
            full_header = "\n".join(potential_header_texts)
            if "CP" in full_header.upper():
                lines = [l.strip() for l in full_header.split('\n') if l.strip()]
                labels = []
                found_cp = False
                for l in lines:
                    lu = l.upper()
                    if "CAT" in lu or "ITEM" in lu or "M.R.P." in lu or "UNIT" in lu or "PRICE" in lu: 
                        if found_cp: break 
                        continue
                    if "CP" in lu: found_cp = True
                    if found_cp:
                        # Clean up label (remove weird characters)
                        lbl = l.strip(" .,|")
                        if lbl: labels.append(lbl)
                if labels:
                    finish_labels = labels

            page_items = []
            for b in blocks:
                if b[6] != 0: continue
                text = b[4].strip()
                if not text: continue
                
                # ── Category Detection ──
                if b[1] < 150:
                    mapped = map_plumber_category(text)
                    if mapped:
                        current_category = mapped
                        continue
                
                # Check if block starts with a product code
                code_match = plumber_code_re.match(text)
                if code_match:
                    code = code_match.group(0).upper()
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    
                    desc_parts = []
                    prices = []
                    
                    for i, ln in enumerate(lines):
                        if i == 0:
                            rem = ln[len(code):].strip()
                            if rem: desc_parts.append(rem)
                        elif i < 6 and not any(c.isdigit() for c in ln[:3]): 
                             desc_parts.append(ln)
                        else:
                             # Extract all numbers of 3-5 digits as prices
                             pms = re.findall(r'(\d{3,5})', ln)
                             for p in pms:
                                 prices.append(p)
                    
                    primary_price = prices[0] if prices else "0"
                    description = " ".join(desc_parts[:5]) 
                    prod_full_name = f"{code} - {description}".strip(" -")
                    
                    # Map collected prices to finish labels
                    variant_prices = {}
                    for i, p_val in enumerate(prices):
                        if i < len(finish_labels):
                            label = finish_labels[i]
                            variant_prices[label] = p_val
                        elif i == 0:
                             variant_prices["CP"] = p_val
                    
                    # Simple image match
                    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
                    best_img_idx = -1
                    best_dist = float("inf")
                    for i_idx, ir in enumerate(img_records):
                        ir_rect = ir["rect"]
                        icx, icy = (ir_rect.x0+ir_rect.x1)/2, (ir_rect.y0+ir_rect.y1)/2
                        dist = ((icx-cx)**2 + (icy-cy)**2)**0.5
                        if dist < best_dist and dist < 700:
                            best_dist = dist
                            best_img_idx = i_idx
                    
                    img_path = img_records[best_img_idx]["path"] if best_img_idx != -1 else ""
                    
                    display_text = f"{prod_full_name}\n"
                    if variant_prices:
                        for lbl, prc in variant_prices.items():
                            display_text += f"MRP ({lbl}) : ` {prc}/-\n"
                    else:
                        display_text += f"MRP : ` {primary_price}/-"
                    
                    page_items.append({
                        "text": display_text.strip(),
                        "name": prod_full_name,
                        "price": primary_price,
                        "variant_prices": variant_prices,
                        "page": page_num + 1,
                        "source": pdf_name,
                        "images": [img_path] if img_path else [],
                        "brand": brand,
                        "category": current_category or "Plumber Products"
                    })
            
            content_list.extend(page_items)
            continue


        if brand == "Aquant" and (page_num + 1) in AQUANT_SKIP_PAGES:
            continue

        # ── 2. Extract products using built-in block grouping (Aquant) ──────
        mapping = [
            (4, "FAUCETS & SHOWERING SYSTEMS IN SPECIAL FINISHES"),
            (8, "CLASSICAL CERAMICS BASINS"),
            (9, "CLASSICAL TOILETS"),
            (10, "FAUCETS & SHOWERING SYSTEMS IN SPECIAL FINISHES"),
            (12, "PRESTIGE COLLECTION BASIN MIXERS"),
            (14, "FAUCETS & SHOWERING SYSTEMS IN SPECIAL FINISHES"),
            (28, "SHOWERING SYSTEMS IN SPECIAL FINISHES"),
            (31, "FAUCETS & SPOUTS IN SPECIAL FINISHES"),
            (32, "SHOWERING SYSTEMS IN SPECIAL FINISHES"),
            (38, "HAND SHOWERS IN SPECIAL FINISHES"),
            (39, "BODY JETS & BODY SHOWERS IN SPECIAL FINISHES"),
            (40, "FAUCETS IN SPECIAL FINISHES"),
            (42, "BATH FITTINGS IN SPECIAL FINISHES"),
            (43, "ALLIED PRODUCTS IN SPECIAL FINISHES"),
            (44, "ACCESSORIES IN SPECIAL FINISHES"),
            (50, "FAUCETS & SHOWERING SYSTEMS IN CHROME FINISH"),
            (52, "SHOWERING SYSTEMS IN CHROME FINISH"),
            (53, "CONCEALED CEILING MOUNTED SHOWERS IN CHROME FINISH"),
            (54, "HAND SHOWERS & HEAD SHOWERS IN CHROME FINISH"),
            (55, "ALLIED PRODUCTS IN CHROME FINISH"),
            (56, "SS SHOWER PANELS IN MATT FINISH"),
            (57, "SHOWER PANELS IN SPECIAL & CHROME FINISH"),
            (58, "FLOOR DRAINS IN STAINLESS STEEL"),
            (59, "FLOOR DRAINS IN SPECIAL FINISHES"),
            (60, "KITCHEN FAUCETS IN SPECIAL & CHROME FINISH"),
            (61, "BATH COMPONENTS"),
            (64, "STONE WASH BASINS"),
            (68, "ARTISTIC WASH BASINS IN UNIQUE MATERIALS"),
            (74, "CERAMIC SANITARY WARE IN SPECIAL FINISHES"),
            (79, "CERAMIC BASINS IN SPECIAL FINISHES"),
            (80, "CERAMIC PEDESTAL WASH BASINS"),
            (81, "CERAMIC BASINS IN WHITE & SPECIAL FINISHES"),
            (82, "CERAMIC WASH BASINS"),
            (86, "INTELLIGENT SMART TOILET AQUANEXX SERIES"),
            (88, "TOILETS"),
            (91, "FLUSH TANKS/PLATES & URINAL SENSORS IN SPECIAL & CHROME FINISH"),
        ]
        
        page_num_1_indexed = page_num + 1
        aquant_cat = None
        for start_pg, cat_name in mapping:
            if page_num_1_indexed >= start_pg:
                aquant_cat = cat_name
            else:
                break
                
        if aquant_cat:
            current_category = aquant_cat
            print(f"   [CAT] Page {page_num_1_indexed} Mapped Category: {current_category}")

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
            # Numeric-dash-numeric: 1424-200
            if re.match(r'^\d{3,}-\d+', w): return True
            # Numeric-dash-alpha: 1234-A
            if re.match(r'^\d{3,}-[A-Z]', w): return True
            # Numeric-alpha-fusion: 7512MI, 7512OG
            if re.match(r'^\d{4,}[A-Z]{1,4}', w): return True
            # Code with space and letters: 1918 AG, 1845 W
            if len(words) > 1 and words[0].isdigit() and len(words[0]) >= 4 and len(words[1]) <= 3:
                return True
            return False



        def is_price_line(text):
            return "MRP" in text or '`' in text or '₹' in text

        # dynamically detect columns
        page_width = page.rect.width
        col_dividers = [0]
        x_starts = sorted(set(round(b[0] / 50) * 50 for b in blocks if b[6] == 0))
        prev = x_starts[0] if x_starts else 0
        for x in x_starts[1:]:
            if x - prev > 85:
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
            
            # Skip the old text based header detection
            if y0 < 25 and len(text) > 10 and not any(c.isdigit() for c in text): continue
            
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

                attach_limit = 35 if prod['has_code'] and not is_code else 80
                if 0 <= vertical_gap <= attach_limit:
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
        
        for p in grouped_products:
            text = p['text'].strip()
            t_comp = re.sub(r'[\s/\-]+', '', text)
            pm = re.search(r'(?:MRP|`|₹)[:.]?`?([\d,]+)', t_comp, re.IGNORECASE)
            block_master_price = pm.group(1).replace(",", "") if pm else ""
            
            clean_lines = [clean_text(l) for l in text.split('\n') if clean_text(l)]
            expanded_lines = []
            for line in clean_lines:
                expanded_lines.extend(split_aquant_segments(line))
            clean_lines = expanded_lines or clean_lines
            
            # Split block into multiple sub-products if multiple codes present
            sub_prods = []
            current_sp = {"name": "", "text": "", "price": ""}
            
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

            sub_prods = []
            code_line_count = 0
            meaningful_detail_lines = []
            for line in clean_lines:
                line_without_price = strip_price_markup(line)
                if line_without_price and is_product_code(line_without_price):
                    code_line_count += 1
                    continue
                if is_price_line(line) or is_aquant_finish_line(line):
                    continue
                if "SIZE" in line.upper() or re.match(r'^\d+(\s*x\s*\d+)+', line, re.IGNORECASE):
                    continue
                meaningful_detail_lines.append(line)

            compact_code_group = code_line_count >= 1 and not meaningful_detail_lines

            if compact_code_group:
                pending = []
                for line in clean_lines:
                    line_without_price = strip_price_markup(line)
                    line_price = extract_price_value(line)
                    line_has_code = bool(line_without_price and is_product_code(line_without_price))

                    if line_has_code:
                        pending.append({
                            "name": line_without_price[:140],
                            "text": line_without_price,
                            "price": line_price or "",
                            "_group_kind": "compact",
                            "_price_source": "inline" if line_price else "pending",
                        })
                        if line_price:
                            sub_prods.extend(pending)
                            pending = []
                        continue

                    if line_price and pending:
                        for pending_item in pending:
                            if not pending_item["price"]:
                                pending_item["price"] = line_price
                                pending_item["_price_source"] = "group_mrp"
                        sub_prods.extend(pending)
                        pending = []
                        continue

                    if pending:
                        for pending_item in pending:
                            pending_item["text"] += "\n" + line

                sub_prods.extend(pending)
            else:
                detail_item = {
                    "name": "",
                    "text": "",
                    "price": "",
                    "_group_kind": "detail",
                    "_price_source": "missing",
                }

                for line in clean_lines:
                    line_without_price = strip_price_markup(line)
                    line_price = extract_price_value(line)
                    price_label = extract_price_label(line)
                    line_has_code = bool(line_without_price and is_product_code(line_without_price))
                    is_size_line = "SIZE" in line.upper() or re.match(r'^\d+(\s*x\s*\d+)+', line, re.IGNORECASE)
                    is_mrp_line = 'MRP' in line.upper()

                    if line_has_code and detail_item["name"]:
                        sub_prods.append(detail_item)
                        detail_item = {
                            "name": line_without_price[:140],
                            "text": line_without_price,
                            "price": line_price or "",
                            "_group_kind": "detail",
                            "_price_source": "inline" if line_price else "missing",
                        }
                        continue

                    if line_has_code and not detail_item["name"]:
                        detail_item["name"] = line_without_price[:140]
                        detail_item["text"] = line_without_price
                        if line_price:
                            detail_item["price"] = line_price
                            detail_item["_price_source"] = "inline"
                        continue

                    if not detail_item["name"] and not is_mrp_line and line_without_price:
                        detail_item["name"] = line_without_price[:140]
                    elif not detail_item["name"] and line_price and price_label:
                        detail_item["name"] = price_label[:140]
                    elif (
                        detail_item["name"]
                        and len(detail_item["name"]) < 72
                        and not is_mrp_line
                        and not is_size_line
                        and not is_aquant_finish_line(line_without_price or line)
                        and line_without_price
                        and line_without_price not in detail_item["name"]
                    ):
                        detail_item["name"] += " - " + line_without_price[:100]

                    if detail_item["text"]:
                        detail_item["text"] += "\n" + line
                    else:
                        detail_item["text"] = detail_item["name"] if detail_item["name"] else line
                        if detail_item["text"] != line:
                            detail_item["text"] += "\n" + line

                    if line_price:
                        detail_item["price"] = line_price
                        detail_item["_price_source"] = "inline"

                if detail_item["name"]:
                    sub_prods.append(detail_item)

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
                    "price": sp["price"] or "0",
                    "page": page_num + 1,
                    "source": pdf_name,
                    "cx": cx,
                    "cy": cy,
                    "images": [],
                    "brand": brand,
                    "category": current_category,
                    "_group_kind": sp.get("_group_kind", "detail"),
                    "_price_source": sp.get("_price_source", "missing"),
                })

        # Image Matching
        available_images = list(img_records)
        page_half = page.rect.width / 2  # column boundary
        _assign_catalog_images_globally(page_products, available_images, page_half)


        detail_candidates = [
            (idx, item) for idx, item in enumerate(page_products)
            if item.get("_group_kind") == "detail"
        ]
        helper_detail_indices = set()

        for p_data in page_products:
            if p_data.get("_group_kind") != "compact":
                continue

            best_match = None
            best_score = float("inf")
            for detail_idx, detail_item in detail_candidates:
                dy = detail_item["cy"] - p_data["cy"]
                if dy < 0 or dy > 140:
                    continue
                score = (dy * 100) + abs(detail_item["cx"] - p_data["cx"])
                if score < best_score:
                    best_score = score
                    best_match = (detail_idx, detail_item)

            if best_match is None:
                continue

            detail_idx, detail_item = best_match
            helper_detail_indices.add(detail_idx)

            detail_name = clean_text(detail_item.get("name", ""))
            variant_name = clean_text(p_data.get("name", ""))
            code_part, finish_part = split_variant_display_name(variant_name)

            if detail_name and detail_name.lower() not in variant_name.lower():
                if finish_part:
                    p_data["name"] = f"{code_part} - {detail_name} - {finish_part}"
                else:
                    p_data["name"] = f"{code_part} - {detail_name}"

            if p_data.get("price") in {"", "0"} and detail_item.get("price") not in {"", "0"}:
                p_data["price"] = detail_item["price"]
                p_data["_price_source"] = "detail"

            detail_lines = [
                line for line in (clean_text(x) for x in detail_item.get("text", "").split("\n"))
                if line and "MRP" not in line.upper()
            ]
            variant_lines = [line for line in (clean_text(x) for x in p_data.get("text", "").split("\n")) if line]

            merged_lines = []
            if variant_lines:
                merged_lines.append(variant_lines[0])
            for line in detail_lines:
                if line not in merged_lines:
                    merged_lines.append(line)
            if p_data.get("price") not in {"", "0"}:
                merged_lines.append(f"MRP : ` {p_data['price']}/-")
            if merged_lines:
                p_data["text"] = "\n".join(merged_lines)

            if not p_data.get("images") and detail_item.get("images"):
                p_data["images"] = list(detail_item["images"])

        family_buckets = {}
        priced_helper_candidates = []
        for idx, item in enumerate(page_products):
            family_key = extract_product_family_key(item.get("name", ""))
            if family_key:
                family_buckets.setdefault(family_key, []).append((idx, item))
            elif str(item.get("price") or "0") not in {"", "0"}:
                priced_helper_candidates.append((idx, item))

        family_meta = {}
        for family_key, bucket in family_buckets.items():
            bucket_items = [item for _, item in bucket]
            family_meta[family_key] = {
                "center_x": sum(item["cx"] for item in bucket_items) / len(bucket_items),
                "center_y": sum(item["cy"] for item in bucket_items) / len(bucket_items),
                "items": bucket_items,
            }

        helper_assignments = {family_key: [] for family_key in family_buckets}
        for helper_idx, helper_item in priced_helper_candidates:
            best_family_key = None
            best_score = float("inf")
            best_dy = 0
            best_dx = 0
            for family_key, meta in family_meta.items():
                dy = helper_item["cy"] - meta["center_y"]
                dx = abs(helper_item["cx"] - meta["center_x"])
                if dy < 0 or dy > 180 or dx > 320:
                    continue
                score = (dy * 100) + dx
                if score < best_score:
                    best_score = score
                    best_family_key = family_key
                    best_dy = dy
                    best_dx = dx
            if best_family_key:
                helper_assignments[best_family_key].append((helper_idx, helper_item, best_dy, best_dx))

        for family_key, bucket in family_buckets.items():
            bucket_items = [item for _, item in bucket]

            priced_items = [item for _, item in bucket if str(item.get("price") or "0") not in {"", "0"}]
            cp_donor = next((item for item in priced_items if extract_variant_token(item.get("name", "")) == "CP"), None)
            special_donor = next(
                (item for item in priced_items if extract_variant_token(item.get("name", "")) not in {"", "CP"}),
                None,
            )
            base_generic_desc = extract_generic_description(cp_donor) if cp_donor else ""
            if not base_generic_desc and priced_items:
                base_generic_desc = extract_generic_description(priced_items[0])

            nearby_helpers = list(helper_assignments.get(family_key, []))
            nearby_helpers.sort(key=lambda row: ((max(row[2], 0) * 100) + row[3], abs(row[2]), row[3]))

            generic_helper = None
            finish_price_map = {}
            for helper_idx, helper_item, _, _ in nearby_helpers:
                helper_label = extract_price_label(helper_item.get("text", "")) or extract_item_finish_label(helper_item)
                helper_generic = extract_generic_description(helper_item)

                if helper_label:
                    finish_price_map[normalize_label(helper_label)] = (helper_item["price"], helper_idx)
                if helper_generic:
                    if generic_helper is None:
                        generic_helper = (helper_idx, helper_item, helper_label)
                    elif base_generic_desc and normalize_label(helper_generic) == normalize_label(base_generic_desc):
                        generic_helper = (helper_idx, helper_item, helper_label)

            donor_generic_desc = ""
            if generic_helper:
                donor_generic_desc = extract_generic_description(generic_helper[1])
            if not donor_generic_desc and special_donor:
                donor_generic_desc = extract_generic_description(special_donor)

            special_price = ""
            if special_donor:
                special_price = special_donor.get("price") or ""
            elif generic_helper and not generic_helper[2]:
                special_price = generic_helper[1].get("price") or ""

            for _, item in bucket:
                variant_token = extract_variant_token(item.get("name", ""))
                finish_label = extract_item_finish_label(item)
                finish_key = normalize_label(finish_label)
                current_price = str(item.get("price") or "0")
                item_generic_desc = extract_generic_description(item)
                cp_price = str(cp_donor.get("price") or "") if cp_donor else ""

                override_with_special = (
                    special_price
                    and variant_token != "CP"
                    and current_price not in {"", "0"}
                    and (
                        not item_generic_desc
                        or normalize_label(item_generic_desc) != normalize_label(donor_generic_desc)
                        or (cp_price and current_price == cp_price and current_price != str(special_price))
                    )
                )

                if finish_key in finish_price_map:
                    mapped_price, helper_idx = finish_price_map[finish_key]
                    if current_price in {"", "0"} or override_with_special:
                        item["price"] = mapped_price
                    helper_detail_indices.add(helper_idx)
                elif variant_token == "CP" and cp_donor and current_price in {"", "0"}:
                    item["price"] = cp_donor.get("price") or current_price
                elif variant_token != "CP" and special_price and (current_price in {"", "0"} or override_with_special):
                    item["price"] = special_price

                if donor_generic_desc and (
                    current_price in {"", "0"}
                    or override_with_special
                    or not item_generic_desc
                    or is_variant_stub_text(item_generic_desc)
                ):
                    merge_variant_details(item, donor_generic_desc, finish_label)
                    if generic_helper:
                        helper_detail_indices.add(generic_helper[0])

        for family_key, bucket in family_buckets.items():
            override = AQUANT_MANUAL_FAMILY_OVERRIDES.get((page_num + 1, family_key))
            if not override:
                continue

            for _, item in bucket:
                variant_token = extract_variant_token(item.get("name", ""))
                finish_label = "" if variant_token in {"", "CP"} else extract_item_finish_label(item)

                if "variant_prices" in override:
                    item["price"] = override["variant_prices"].get(variant_token, item.get("price", "0"))
                elif variant_token == "CP" and override.get("cp_price"):
                    item["price"] = override["cp_price"]
                elif variant_token != "CP" and override.get("variant_price"):
                    item["price"] = override["variant_price"]

                if override.get("generic_name"):
                    if variant_token == "":
                        item["name"] = f"{family_key} - {override['generic_name']}"
                    merge_variant_details(item, override["generic_name"], finish_label)

        for item in page_products:
            normalize_aquant_item(item)

        apply_aquant_page_code_overrides(page_num, page_products, available_images)

        for item in page_products:
            family_key = extract_product_family_key(item.get("name", ""))
            variant_token = extract_variant_token(item.get("name", ""))
            exact_name = AQUANT_EXACT_ITEM_OVERRIDES.get((page_num + 1, family_key, variant_token))
            if not exact_name:
                continue

            item["name"] = exact_name
            text_lines = [exact_name]
            override = AQUANT_MANUAL_FAMILY_OVERRIDES.get((page_num + 1, family_key))
            if override and override.get("generic_name") and override["generic_name"] not in text_lines:
                text_lines.append(override["generic_name"])
            if str(item.get("price") or "0") not in {"", "0"}:
                text_lines.append(f"MRP : ` {item['price']}/-")
            item["text"] = "\n".join(text_lines)

        apply_aquant_special_finish_image_rows(page_num, page_products, available_images)

        image_records_by_path = {
            ir["path"]: ir for ir in available_images
            if ir.get("rect") is not None and ir.get("path")
        }
        family_image_map = {family_key: [] for family_key in family_buckets}
        for family_key, bucket in family_buckets.items():
            seen_paths = set()
            for _, item in bucket:
                for img_path in item.get("images", []):
                    if img_path in image_records_by_path and img_path not in seen_paths:
                        family_image_map[family_key].append(img_path)
                        seen_paths.add(img_path)

        claimed_image_paths = {
            img_path
            for paths in family_image_map.values()
            for img_path in paths
        }

        for img_path, ir in image_records_by_path.items():
            if img_path in claimed_image_paths:
                continue

            img_rect = ir["rect"]
            img_cx = (img_rect.x0 + img_rect.x1) / 2
            img_cy = (img_rect.y0 + img_rect.y1) / 2
            i_col = 0 if img_cx < page_half else 1
            best_family_key = None
            best_score = float("inf")

            for family_key, bucket in family_buckets.items():
                local_best = float("inf")
                for _, item in bucket:
                    p_cx = item.get("cx") or 0
                    p_cy = item.get("cy") or 0
                    p_col = 0 if p_cx < page_half else 1
                    col_penalty = 0 if p_col == i_col else 400
                    dx = abs(img_cx - p_cx)
                    dy = img_cy - p_cy
                    v_penalty = 0
                    if dy > 70: v_penalty = 220
                    if dy < -480: v_penalty = 180

                    score = (dx ** 2 + dy ** 2) ** 0.5 + v_penalty + col_penalty
                    if score < local_best:
                        local_best = score

                if local_best < best_score:
                    best_score = local_best
                    best_family_key = family_key

            if best_family_key and best_score < 750:


                family_image_map[best_family_key].append(img_path)
                claimed_image_paths.add(img_path)

        for family_key, bucket in family_buckets.items():
            family_paths = family_image_map.get(family_key, [])
            if not family_paths:
                continue

            for _, item in bucket:
                if item.get("images"):
                    continue

                best_path = None
                best_score = float("inf")
                for img_path in family_paths:
                    ir = image_records_by_path.get(img_path)
                    if not ir:
                        continue
                    img_rect = ir["rect"]
                    img_cx = (img_rect.x0 + img_rect.x1) / 2
                    img_cy = (img_rect.y0 + img_rect.y1) / 2
                    p_cx = item.get("cx") or 0
                    p_cy = item.get("cy") or 0
                    p_col = 0 if p_cx < page_half else 1
                    i_col = 0 if img_cx < page_half else 1
                    col_penalty = 0 if p_col == i_col else 400
                    dx = abs(img_cx - p_cx)
                    dy = img_cy - p_cy
                    v_penalty = 0
                    if dy > 70: v_penalty = 220
                    if dy < -480: v_penalty = 180
                    score = (dx ** 2 + dy ** 2) ** 0.5 + v_penalty + col_penalty
                    if score < best_score and score < 750:



                        best_score = score
                        best_path = img_path

                if best_path:
                    item["images"] = [best_path]

        page_products = [
            item for idx, item in enumerate(page_products)
            if not (
                idx in helper_detail_indices
                and item.get("_group_kind") == "detail"
                and not is_product_code(item.get("name", ""))
            )
        ]

        _prune_suspicious_page_images(page_products, available_images)

        for p in page_products:
            if not extract_product_family_key(p.get("name", "")):
                continue
            if "cx" in p: del p["cx"]
            if "cy" in p: del p["cy"]


            if "_group_kind" in p: del p["_group_kind"]
            if "_price_source" in p: del p["_price_source"]
            content_list.append(p)

    return content_list

    return content_list


def chunk_content(content_list):
    return content_list
