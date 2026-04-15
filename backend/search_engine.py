import numpy as np
import re
import os
import json
import threading

import cloud_storage
from app_paths import resolve_data_dir

import sys
is_frozen = getattr(sys, 'frozen', False)
EXE_DIR = os.path.dirname(os.path.abspath(sys.executable)) if is_frozen else os.path.dirname(os.path.abspath(__file__))
_MEIPASS = getattr(sys, '_MEIPASS', EXE_DIR)

BUNDLED_DIR = EXE_DIR
DATA_DIR = resolve_data_dir(is_frozen, EXE_DIR)

# Priority path for search index
INDEX_FILE_PERSISTENT = os.path.join(DATA_DIR, "search_index_v2.json")
INDEX_FILE_BUNDLED = os.path.join(BUNDLED_DIR, "search_index_v2.json")
INDEX_FILE = INDEX_FILE_PERSISTENT

# Lazy model loading - loads in background only when needed
AI_AVAILABLE = False
model = None
_model_lock = threading.Lock()
_model_loading = False

def _load_model_background():
    global model, AI_AVAILABLE, _model_loading
    try:
        print("Loading Semantic Model in background...")
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer('all-MiniLM-L6-v2')
        with _model_lock:
            model = m
            AI_AVAILABLE = True
        print("Semantic Model Loaded OK.")
    except Exception as e:
        print(f"Warning: Semantic model failed to load (possibly OOM): {e}")
        import traceback
        traceback.print_exc()
    finally:
        _model_loading = False

def ensure_model_loaded():
    """Trigger model loading if not already started."""
    global _model_loading
    
    if model is None and not _model_loading:
        _model_loading = True
        print("Lazy Loading triggered for Semantic Model...")
        threading.Thread(target=_load_model_background, daemon=True).start()

# REMOVED: immediate load on import
# ensure_model_loaded()

# Try loading FAISS
FAISS_AVAILABLE = False
faiss = None
try:
    import faiss as _faiss
    faiss = _faiss
    FAISS_AVAILABLE = True
    print("FAISS Loaded OK.")
except Exception as e:
    print(f"Warning: FAISS not available: {e}")


# ---- Global State ----
stored_items = []
keyword_index = {}   # word -> [item_indices]
vector_index  = None # FAISS index
search_cache  = {}   # query -> results
catalog_summary_cache = None # Saved dashboard index
item_code_meta_cache = {}
_index_cache_signature = None
_image_path_cache = None


# INDEX_FILE is now dynamically determined in load_index
SEARCH_INDEX_OBJECT_PATH = os.getenv("SUPABASE_SEARCH_INDEX_PATH", "search/search_index_v2.json")

STATIC_IMAGES_DIR = os.path.join(BUNDLED_DIR, "static", "images")

# Minimum file size (bytes) for a valid product image.
# Images below this are icons, colour swatches, or small decorative elements from the PDF.
_MIN_PRODUCT_IMAGE_SIZE = 8000

_LEADING_CODE_WITH_VARIANT_RE = re.compile(
    r'^\s*((?:[A-Z]{1,4}-\d[A-Z0-9\+\-\ ]*|\d[A-Z0-9\+\-\ ]*))(?:\s+([A-Z0-9+]{1,12}))?',
    re.IGNORECASE,
)
_KNOWN_FINISH_LABELS = {
    "AB": "Antique Bronze",
    "AC": "Antique Chrome",
    "AN": "Antique Nickel",
    "B": "Glossy Black",
    "BC": "Beige Caramel",
    "BCG": "Black Champagne Gold",
    "BG": "Brushed Gold",
    "BCK": "Matt Black",
    "BRG": "Brushed Rose Gold",
    "BSS": "Brushed Stainless Steel Finish",
    "CB": "Chrome Black",
    "CGY": "Chrome Grey",
    "CH": "Chrome",
    "CM": "Carrara Marble",
    "CNG": "Champagne Gold",
    "CP": "Chrome Plated",
    "CW": "Chrome White",
    "G": "Gold",
    "GB": "Glossy Black",
    "GG": "Graphite Grey/Glossy Gold",
    "GM": "Gun Metal",
    "GRY": "Matt Grey",
    "LG": "Lunar Grey",
    "MB": "Matt Black",
    "MG": "Matt Grey",
    "MI": "Matt Ivory",
    "LM": "Lavender Marble (Chevron Amethyst)",
    "MW": "Matt White/White",
    "OG": "Olive Green",
    "ORB": "Oil Rubbed Bronze",
    "RB": "Royal Blue",
    "RG": "Rose Gold",
    "BM": "Marquina Marble",
    "PP": "Pink Paradise (Pink Onyx)",
    "RGB": "Rose Gold/Matt Black",
    "RGD": "Rose Gold",
    "RGW": "Rose Gold/Matt White",
    "RN": "Royal Navy",
    "SB": "Sky Blue",
    "SG": "Seafoam Green",
    "SN": "Satin Nickel",
    "SSF": "Brushed Stainless Steel",
    "TCR": "Terracotta Red",
    "W": "White",
    "WCG": "White Champagne Gold",
    "WG": "White Glass",
    "WN": "Walnut",
    "WRG": "White Rose Gold",
    "WTE": "Matt White",
    # Kohler Finishes
    "0": "White",
    "7": "Black Black",
    "AF": "Vibrant French Gold",
    "BN": "Vibrant Brushed Nickel",
    "BV": "Vibrant Brushed Bronze",
    "BGD": "Vibrant Moderne Brushed Gold",
    "2MB": "Vibrant Brushed Moderne Brass",
    "TT": "Vibrant Titanium",
    "VS": "Vibrant Stainless",
    "BL": "Matte Black",
    "GP1": "Gold",
    "GP2": "Brushed Gold",
}
_KNOWN_FINISH_CODES = tuple(sorted(_KNOWN_FINISH_LABELS.keys(), key=len, reverse=True))


def _image_file_size(image_path: str) -> int:
    """Return the file size of a /static/images/… path, or -1 if missing."""
    if not image_path:
        return -1
    rel = str(image_path).lstrip("/")
    rel = rel.replace("static/images/", "", 1).replace("static/", "", 1)
    full = os.path.abspath(os.path.normpath(os.path.join(STATIC_IMAGES_DIR, rel)))
    if not full.startswith(os.path.abspath(STATIC_IMAGES_DIR)):
        return -1
    try:
        return os.path.getsize(full)
    except OSError:
        return -1


def _is_cover_page_image(image_path: str) -> bool:
    """True when the image clearly comes from a PDF cover / title page."""
    if not image_path:
        return False
    basename = os.path.basename(image_path)
    # Matches patterns like  Brand_..._p0_i3.jpg  and  Brand_..._p1_i0.jpg
    import re as _re
    return bool(_re.search(r'_p[012]_i', basename))


def _normalize_variant_token(token: str) -> str:
    token = re.sub(r'\s+', '', str(token or "").upper())
    token = token.strip("-_/+")
    if not token:
        return ""
    return "+".join(part for part in token.split("+") if part)


def _is_likely_finish_token(token: str) -> bool:
    normalized = _normalize_variant_token(token)
    if not normalized:
        return False

    parts = [part for part in normalized.split("+") if part]
    if not parts:
        return False

    return all(part in _KNOWN_FINISH_LABELS for part in parts)


def _split_attached_finish_token(code: str):
    normalized = str(code or "").strip().upper()
    if not normalized:
        return "", ""

    # Plain numeric model codes like "4000" or "4010" should stay intact.
    # Treating the trailing 0/7 as a finish token breaks exact code search.
    if normalized.isdigit():
        return normalized, ""

    combo_match = re.match(
        r'^((?:[A-Z]{1,4}-\d[A-Z0-9-]*|\d[\d-]*))([A-Z]{1,4}(?:\+[A-Z]{1,4})+)$',
        normalized,
    )
    if combo_match:
        base_code = combo_match.group(1).strip()
        variant_code = _normalize_variant_token(combo_match.group(2))
        if base_code and _is_likely_finish_token(variant_code):
            return base_code, variant_code

    if "-" in normalized:
        maybe_base, maybe_variant = normalized.rsplit("-", 1)
        maybe_variant = _normalize_variant_token(maybe_variant)
        if maybe_base and _is_likely_finish_token(maybe_variant) and re.search(r'\d', maybe_base):
            return maybe_base.strip(), maybe_variant

    for finish_code in _KNOWN_FINISH_CODES:
        if not normalized.endswith(finish_code):
            continue
        maybe_base = normalized[:-len(finish_code)].strip()
        if maybe_base and re.search(r'\d', maybe_base):
            return maybe_base, finish_code

    return normalized, ""


def _format_finish_label(variant_code: str) -> str:
    normalized = _normalize_variant_token(variant_code)
    if not normalized:
        return ""
    return " + ".join(_KNOWN_FINISH_LABELS.get(part, part) for part in normalized.split("+") if part)

def _clean_display_text(text: str) -> str:
    """Normalize common mojibake/bullet artifacts for UI display."""
    if not text:
        return ""
    s = str(text)
    # Common UTF-8 mojibake sequences from PDF bullets/dashes.
    for bad in ("â€¢", "â€“", "â€”", "â€", "â–=", "â–"):
        s = s.replace(bad, "•")
    # Normalize bullet-like glyphs to a simple dash for cleaner UI.
    for bullet in ("•", "●", "▪", "◦", "◾", "■"):
        s = s.replace(bullet, "-")
    # Collapse extra spaces introduced by replacements.
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()

def _parse_code_metadata(raw_text: str):
    text = str(raw_text or "").strip()
    if not text:
        return {
            "base_code": "",
            "variant_code": "",
            "full_code": "",
            "base_compact": "",
            "variant_compact": "",
            "full_compact": "",
            "finish_label": "",
        }

    header = text.splitlines()[0].strip()
    header = re.split(r'\s+-\s+', header, maxsplit=1)[0].strip()
    header = re.sub(r'\bMRP\b.*$', '', header, flags=re.IGNORECASE).strip(" -:")
    if not header:
        return {
            "base_code": "",
            "variant_code": "",
            "full_code": "",
            "base_compact": "",
            "variant_compact": "",
            "full_compact": "",
            "finish_label": "",
        }

    match = _LEADING_CODE_WITH_VARIANT_RE.match(header)
    if match:
        base_code = (match.group(1) or "").strip().upper()
        variant_code = _normalize_variant_token(match.group(2))
        if variant_code and not _is_likely_finish_token(variant_code):
            variant_code = ""
        if not variant_code:
            base_code, variant_code = _split_attached_finish_token(base_code)
    else:
        base_code, variant_code = _split_attached_finish_token(header.upper())

    full_code = base_code
    if variant_code:
        full_code = f"{base_code} {variant_code}".strip()

    return {
        "base_code": base_code,
        "variant_code": variant_code,
        "full_code": full_code,
        "base_compact": _compact_alnum(base_code),
        "variant_compact": _compact_alnum(variant_code),
        "full_compact": _compact_alnum(full_code),
        "finish_label": _format_finish_label(variant_code),
    }


def _get_item_code_metadata(item):
    cache_key = id(item)
    cached = item_code_meta_cache.get(cache_key)
    if isinstance(cached, dict) and cached.get("full_code") is not None:
        return cached

    # Prefer any code metadata already present on the item. This matters for
    # catalogs where the stored index has been normalized offline (for example
    # Aquant families like 1330 CI/IR/MT/GS/AO) and avoids re-parsing raw text
    # back into an older, less accurate split.
    stored_base = str(item.get("base_code", "")).strip().upper()
    stored_variant = _normalize_variant_token(item.get("variant_code", ""))
    stored_search = str(item.get("search_code", "")).strip().upper()
    if stored_base:
        full_code = stored_search or stored_base
        if not full_code.startswith(stored_base):
            full_code = stored_base
            if stored_variant:
                full_code = f"{stored_base} {stored_variant}".strip()
        elif not stored_variant and full_code != stored_base:
            stored_variant = _normalize_variant_token(full_code[len(stored_base):].strip())

        meta = {
            "base_code": stored_base,
            "variant_code": stored_variant,
            "full_code": full_code,
            "base_compact": _compact_alnum(stored_base),
            "variant_compact": _compact_alnum(stored_variant),
            "full_compact": _compact_alnum(full_code),
            "finish_label": item.get("finish_label") or _format_finish_label(stored_variant),
        }
        item_code_meta_cache[cache_key] = meta
        return meta

    for raw in (
        item.get("code", ""),
        item.get("name", ""),
        str(item.get("text", "")).split("\n")[0],
    ):
        meta = _parse_code_metadata(raw)
        if meta["base_code"]:
            item["base_code"] = meta["base_code"]
            item["variant_code"] = meta["variant_code"]
            item["search_code"] = meta["full_code"]
            if meta["finish_label"] and not item.get("finish_label"):
                item["finish_label"] = meta["finish_label"]
            item_code_meta_cache[cache_key] = meta
            return meta

    empty = _parse_code_metadata("")
    item_code_meta_cache[cache_key] = empty
    return empty


def _enrich_items_for_search(items):
    for item in items:
        _get_item_code_metadata(item)


def _item_quality_bonus(item) -> float:
    bonus = 0.0
    price = str(item.get("price") or "").strip()
    name = str(item.get("name") or "").strip()

    if price and price != "0":
        bonus += 60.0
    else:
        bonus -= 80.0

    if item.get("images"):
        bonus += 18.0

    if " - " in name:
        bonus += 10.0
    if "+ -" in name or name.endswith(" +"):
        bonus -= 45.0
    if len(name) >= 24:
        bonus += 6.0

    return bonus


def _sanitize_item_images(items):
    """
    Skipped since images are now correctly pre-processed and extracted by model number.
    """
    pass


def _normalize_item_images(items):
    for item in items or []:
        best_image = _best_item_image(item)
        if best_image:
            item["images"] = [best_image]

def save_index():
    global stored_items, keyword_index
    data = {
        "stored_items": stored_items,
        "keyword_index": keyword_index
    }
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"Index saved to {INDEX_FILE}")

    if cloud_storage.is_enabled():
        try:
            cloud_storage.upload_file(
                cloud_storage.SYSTEM_BUCKET,
                SEARCH_INDEX_OBJECT_PATH,
                INDEX_FILE,
                "application/json",
            )
            print("Index synced to cloud storage.")
        except Exception as e:
            print(f"Warning: failed to sync index to cloud storage: {e}")

def load_index(force: bool = False):
    global stored_items, keyword_index, vector_index, search_cache, catalog_summary_cache, item_code_meta_cache, _index_cache_signature
    
    # Decide which index file to use
    index_file = INDEX_FILE_PERSISTENT
    if not os.path.exists(index_file):
        index_file = INDEX_FILE_BUNDLED
        
    if not os.path.exists(index_file) and cloud_storage.is_enabled():
        try:
            restored = cloud_storage.download_to_path(
                cloud_storage.SYSTEM_BUCKET,
                SEARCH_INDEX_OBJECT_PATH,
                index_file,
            )
            if restored:
                print("Restored search index from cloud storage.")
        except Exception as e:
            print(f"Warning: failed to restore index from cloud storage: {e}")

    if os.path.exists(index_file):
        try:
            signature = (index_file, os.path.getmtime(index_file), os.path.getsize(index_file))
            if not force and stored_items and _index_cache_signature == signature:
                return True

            with open(index_file, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
                stored_items = data.get("stored_items", [])
                keyword_index = data.get("keyword_index", {})
            print(f"Index loaded: {len(stored_items)} items from {index_file}")
            _index_cache_signature = signature

            item_code_meta_cache = {}
            _enrich_items_for_search(stored_items)

            # Strip bad/wrong product images (cover logos, tiny icons, missing files)
            _sanitize_item_images(stored_items)
            _normalize_item_images(stored_items)

            # Reset caches
            search_cache = {}
            catalog_summary_cache = None

            # Rebuild FAISS in background to avoid blocking API
            if AI_AVAILABLE and FAISS_AVAILABLE and stored_items:
                threading.Thread(target=_rebuild_faiss_background, daemon=True).start()

            return True
        except Exception as e:
            print(f"Error loading index: {e}")
    return False

def _rebuild_faiss_background():
    global vector_index
    print("Background FAISS rebuild started...")
    try:
        texts = [item["text"] for item in stored_items]
        batch_size = 256
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = model.encode(batch_texts, convert_to_numpy=True, show_progress_bar=False)
            all_embeddings.append(batch_embeddings)
        
        embeddings = np.vstack(all_embeddings).astype(np.float32)
        faiss.normalize_L2(embeddings)
        dim = embeddings.shape[1]
        v_idx = faiss.IndexFlatIP(dim)
        v_idx.add(embeddings)
        vector_index = v_idx
        print("Background FAISS rebuild complete.")
    except Exception as e:
        print(f"FAISS rebuild failed: {e}")

def reset_index():
    global stored_items, keyword_index, vector_index, search_cache, catalog_summary_cache, item_code_meta_cache
    stored_items   = []
    keyword_index  = {}
    vector_index   = None
    search_cache   = {}
    catalog_summary_cache = None
    item_code_meta_cache = {}
    if os.path.exists(INDEX_FILE):
        os.remove(INDEX_FILE)
    if cloud_storage.is_enabled():
        try:
            cloud_storage.delete_object(cloud_storage.SYSTEM_BUCKET, SEARCH_INDEX_OBJECT_PATH)
        except Exception as e:
            print(f"Warning: failed to delete cloud search index: {e}")


def _normalize(text, strip_in=False):
    # Remove common separators and non-essential chars
    t = re.sub(r'[\s\-\/\.\_\u2013\u2014]+', '', text.lower())
    if strip_in:
        t = t.replace('in', '')
    return t

def _code_like(text: str) -> bool:
    return bool(re.search(r'[a-z]', text.lower())) and bool(re.search(r'\d', text))

def _compact_alnum(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', text.lower())

def _build_image_path_cache():
    global _image_path_cache
    if _image_path_cache is not None:
        return _image_path_cache

    cache = {}
    if os.path.isdir(STATIC_IMAGES_DIR):
        for root, _, files in os.walk(STATIC_IMAGES_DIR):
            for filename in files:
                stem = os.path.splitext(filename)[0]
                compact = _compact_alnum(stem)
                if not compact:
                    continue
                rel_dir = os.path.relpath(root, STATIC_IMAGES_DIR).replace("\\", "/")
                rel_path = f"{filename}" if rel_dir == "." else f"{rel_dir}/{filename}"
                public_path = f"/static/images/{rel_path}"
                cache.setdefault(compact, []).append(public_path)

    _image_path_cache = cache
    return cache


def _best_item_image(item):
    """Prefer an exact model-name image when one exists on disk."""
    code_meta = _get_item_code_metadata(item)
    candidate_codes = []
    for key in ("full_code", "search_code", "base_code"):
        value = str(item.get(key, "") or code_meta.get(key, "")).strip()
        if value:
            candidate_codes.append(value)

    # Preserve already attached images if they exist and resolve correctly.
    for img_path in item.get("images") or []:
        if not img_path:
            continue
        if _image_file_size(img_path) >= 0:
            return img_path

    image_cache = _build_image_path_cache()
    for code in candidate_codes:
        compact_code = _compact_alnum(code)
        if not compact_code:
            continue
        matches = image_cache.get(compact_code)
        if matches:
            return matches[0]

    images = item.get("images") or []
    return images[0] if images else None


def _special_family_override_items(query_code_meta, brand_lower: str):
    """
    Some product families intentionally span multiple nearby codes.
    Keep these grouped so search returns the intended set instead of
    leaking in visually similar combo products.
    """
    base_compact = query_code_meta.get("base_compact", "")
    variant_compact = query_code_meta.get("variant_compact", "")
    if base_compact != "1333" or variant_compact:
        return []

    allowed_compacts = {"1333cm", "1333bm", "1333pp", "1333rb", "11333lm"}
    picked = []
    for item in stored_items:
        if brand_lower and brand_lower != "all" and _item_brand(item) != brand_lower:
            continue
        meta = _get_item_code_metadata(item)
        if meta.get("full_compact") in allowed_compacts:
            picked.append(item)

    order = {code: idx for idx, code in enumerate(["1333cm", "1333bm", "11333lm", "1333pp", "1333rb"])}
    picked.sort(key=lambda item: order.get(_get_item_code_metadata(item).get("full_compact", ""), 999))
    return picked

def _code_relaxed(compact_code: str) -> str:
    # Handle common OCR confusion in model codes: O/0 and I/L/1.
    return (
        (compact_code or "")
        .lower()
        .replace("o", "0")
        .replace("i", "1")
        .replace("l", "1")
    )

def _extract_compound_code_tokens(text: str):
    cleaned = re.sub(r'[\r\n\t]+', ' ', str(text or '').lower())
    tokens = re.findall(r'\b(?:[a-z]{1,4}[-/]?\d{2,}|\d{3,})(?:\s+[a-z]{1,3}){1,2}\b', cleaned)
    seen = set()
    ordered = []
    for tok in tokens:
        normalized = re.sub(r'\s+', ' ', tok).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered

def _is_code_or_model_query(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    tokens = re.findall(r'[a-z0-9/\-\+]+', q)
    if not tokens:
        return False

    if _extract_compound_code_tokens(q):
        return True

    # If any token itself looks like a model/code, treat as strict code query
    for tok in tokens:
        if re.fullmatch(r'[a-z]{1,5}[-/]?\d{2,}[a-z0-9/-]*', tok):
            return True

    # Single-token numeric or mixed token queries are likely direct code searches
    if len(tokens) == 1 and re.fullmatch(r'\d{3,}', tokens[0]):
        return True
    if len(tokens) == 1 and bool(re.search(r'[a-z]', tokens[0])) and bool(re.search(r'\d', tokens[0])) and len(tokens[0]) >= 4:
        return True
    numeric_tokens = [tok for tok in tokens if re.fullmatch(r'\d{3,}', tok)]
    if numeric_tokens:
        known_brands = {"kohler", "aquant", "plumber"}
        if len(tokens) <= 3 and any(tok in known_brands for tok in tokens):
            return True

    return False

def _extract_model_tokens(text: str):
    # Handles model patterns like K-12345IN, 9272, 2594CP, etc.
    seen = set()
    ordered = []

    for tok in _extract_compound_code_tokens(text):
        if tok not in seen:
            seen.add(tok)
            ordered.append(tok)

    for tok in re.findall(r'[a-z]{1,4}[-/]?\d{2,}[a-z0-9/-]*|\b\d{3,}\b', text.lower()):
        if tok not in seen:
            seen.add(tok)
            ordered.append(tok)

    return ordered


def _exact_name_variants(item):
    name = str(item.get("name") or "").strip()
    text = str(item.get("text") or "").strip()
    first_line = text.split("\n")[0].strip() if text else name
    base_line = first_line or name

    variants = []
    for raw in (name, first_line, base_line):
        cleaned = raw.strip()
        if cleaned and cleaned not in variants:
            variants.append(cleaned)

    parts = [part.strip() for part in base_line.split(" - ") if part.strip()]
    
    # NEW: Handle Kohler style "Title (Code)" or "Title Code"
    if not parts or len(parts) < 2:
        # Try finding a bracketed code or a trailing K- code
        m = re.search(r'^(.*?)\s*[\(\[]?\s*(K-\d[A-Z0-9-]*)\s*[\)\]]?$', base_line, re.IGNORECASE)
        if m:
            parts = [m.group(1).strip(), m.group(2).strip()]
            
    if parts:
        head = parts[0]
        tail_parts = parts[1:] if (_extract_model_tokens(head) or bool(re.search(r'\d', head))) else parts
        if tail_parts:
            joined_dash = " - ".join(tail_parts)
            joined_space = " ".join(tail_parts)
            for raw in (joined_dash, joined_space):
                cleaned = raw.strip()
                if cleaned and cleaned not in variants:
                    variants.append(cleaned)

    return variants


def _exact_name_score(item, query: str) -> float:
    query = (query or "").strip()
    if not query:
        return 0.0

    query_lower = query.lower()
    query_compact = _compact_alnum(query)
    query_has_digits = bool(re.search(r'\d', query_lower))
    query_norm = _normalize(query, strip_in=query_has_digits)

    best = 0.0
    variants = _exact_name_variants(item)
    if not variants:
        return 0.0

    for idx, variant in enumerate(variants):
        variant_lower = variant.lower()
        variant_compact = _compact_alnum(variant)
        variant_norm = _normalize(variant, strip_in=query_has_digits)

        if query_compact and variant_compact == query_compact:
            score = 4200.0 - (idx * 10.0)
            best = max(best, score)
            continue

        if query_norm and len(query_norm) >= 3 and variant_norm == query_norm:
            score = 4100.0 - (idx * 10.0)
            best = max(best, score)
            continue

        if variant_lower == query_lower:
            score = 4000.0 - (idx * 10.0)
            best = max(best, score)

    return best

def _item_brand(item):
    brand = (item.get("brand") or "").strip()
    if brand:
        return brand.lower()
    source = str(item.get("source") or "").lower()
    if "kohler" in source:
        return "kohler"
    if "aquant" in source:
        return "aquant"
    if "plumber" in source:
        return "plumber"
    return ""

def add_to_index(_unused_embeddings, items):
    global stored_items, keyword_index, vector_index, search_cache

    search_cache = {}
    _enrich_items_for_search(items)
    start_idx = len(stored_items)
    stored_items.extend(items)

    for i, item in enumerate(items):
        idx = start_idx + i
        text = item.get("text", "")
        name = item.get("name", "")
        search_blob = f"{name}\n{text}".strip()
        blob_lower = search_blob.lower()

        # Build list of unique tokens to index
        words_to_index = set()

        # 1. Broad split on any separator (including en-dash, dots, etc)
        tokens = re.split(r'[\s\-\/\.\_\u2013\u2014\(\)\[\],:;]+', blob_lower)
        for w in tokens:
            w = w.strip()
            if len(w) >= 2:
                words_to_index.add(w)
                # If it looks like model/code like K12345IN, store normalized variant as well.
                if _code_like(w):
                    words_to_index.add(_normalize(w, strip_in=True))

        # 2. Extract model/code tokens explicitly (e.g. k-12345in, 9272, 2594cp)
        for model_tok in _extract_model_tokens(search_blob):
            words_to_index.add(model_tok)
            norm_tok = _normalize(model_tok, strip_in=True)
            compact_tok = _compact_alnum(model_tok)
            if len(norm_tok) >= 3:
                words_to_index.add(norm_tok)
            if len(compact_tok) >= 3:
                words_to_index.add(compact_tok)

        code_meta = _get_item_code_metadata(item)
        for meta_key in ("base_code", "variant_code", "full_code"):
            meta_value = code_meta.get(meta_key, "")
            if not meta_value:
                continue
            words_to_index.add(meta_value.lower())
            compact_value = _compact_alnum(meta_value)
            normalized_value = _normalize(meta_value, strip_in=True)
            if len(compact_value) >= 3:
                words_to_index.add(compact_value)
            if len(normalized_value) >= 3:
                words_to_index.add(normalized_value)

        # 3. Add normalized name and first text slice for combined code-name queries
        norm_name = _normalize(name, strip_in=True)
        norm_head = _normalize(text[:120], strip_in=True)
        if len(norm_name) >= 3:
            words_to_index.add(norm_name)
        if len(norm_head) >= 3:
            words_to_index.add(norm_head)

        for w in words_to_index:
            if w:
                keyword_index.setdefault(w, []).append(idx)

    # FAISS Vector Indexing
    if AI_AVAILABLE and FAISS_AVAILABLE:
        try:
            texts      = [item["text"] for item in items]
            embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            embeddings = embeddings.astype(np.float32)
            faiss.normalize_L2(embeddings)

            if vector_index is None:
                dim = embeddings.shape[1]
                vector_index = faiss.IndexFlatIP(dim)

            vector_index.add(embeddings)
            print(f"Indexed {len(items)} blocks (total: {len(stored_items)})")
        except Exception as e:
            print(f"Embedding error: {e}")

    save_index()



def search(query: str, smart: bool = False, brand: str = None):
    global stored_items, keyword_index
    
    query = query.strip()
    if not query:
        return []
        
    load_index()
    if not stored_items:
        return []

    brand_lower = (brand or "").strip().lower()
    is_all_brand = (not brand_lower) or (brand_lower == "all")
    cache_key = f"{query}|{smart}|{brand_lower}"
    if cache_key in search_cache:
        return search_cache[cache_key]

    query_lower = query.lower()
    query_words = [w for w in re.split(r'[\s\-\/\.\_\u2013\u2014]+', query_lower) if len(w) >= 2]
    query_alnum = re.sub(r'[^a-z0-9]+', '', query_lower)
    query_has_digits = bool(re.search(r'\d', query_lower))
    is_code_query = _is_code_or_model_query(query)
    query_norm = _normalize(query, strip_in=query_has_digits)
    query_model_tokens = _extract_model_tokens(query)
    query_model_norms = {_normalize(tok, strip_in=True) for tok in query_model_tokens if len(tok) >= 2}
    query_compact = _compact_alnum(query)
    query_code_meta = _parse_code_metadata(query)
    query_base_compact = query_code_meta.get("base_compact", "")
    query_variant_compact = query_code_meta.get("variant_compact", "")
    query_full_compact = query_code_meta.get("full_compact", "")

    special_family = _special_family_override_items(query_code_meta, brand_lower)
    if special_family:
        search_cache[cache_key] = special_family
        return special_family

    # Prefer an explicit code-like token from the query (e.g. "kohler K-28220T-SL-0").
    strict_query_compact = ""
    if query_full_compact:
        strict_query_compact = query_full_compact
    for tok in query_model_tokens:
        if strict_query_compact:
            break
        tok_compact = _compact_alnum(tok)
        if len(tok_compact) >= 3 and bool(re.search(r'[a-z]', tok_compact)) and bool(re.search(r'\d', tok_compact)):
            strict_query_compact = tok_compact
            break
    if not strict_query_compact:
        for tok in query_model_tokens:
            tok_compact = _compact_alnum(tok)
            if len(tok_compact) >= 3 and tok_compact.isdigit():
                strict_query_compact = tok_compact
                break
    if not strict_query_compact:
        strict_query_compact = query_compact

    # 1. RETRIEVE CANDIDATES FAST
    candidate_indices = set()
    lookup_keys = set(query_words)
    if len(query_alnum) >= 3:
        lookup_keys.add(query_alnum)
    if len(query_norm) >= 3:
        lookup_keys.add(query_norm)
    for model_tok in query_model_tokens:
        if len(model_tok) >= 2:
            lookup_keys.add(model_tok)
    for model_norm in query_model_norms:
        if len(model_norm) >= 3:
            lookup_keys.add(model_norm)
    for meta_value in (
        query_code_meta.get("base_code", ""),
        query_code_meta.get("variant_code", ""),
        query_code_meta.get("full_code", ""),
        query_base_compact,
        query_variant_compact,
        query_full_compact,
    ):
        if len(str(meta_value or "").strip()) >= 1:
            lookup_keys.add(str(meta_value).lower())

    for key in lookup_keys:
        if key in keyword_index:
            candidate_indices.update(keyword_index[key])
        
    # If no direct hits, do a partial lookup fallback.
    if not candidate_indices and (len(query_alnum) >= 3 or len(query_lower) >= 4):
        for kindex in keyword_index:
            if (query_alnum and query_alnum in kindex) or (query_lower in kindex):
                candidate_indices.update(keyword_index[kindex])
                if len(candidate_indices) > 300:
                    break

    if not candidate_indices:
        # For model/code queries, do a strict full scan fallback.
        if is_code_query:
            candidate_indices = set(range(len(stored_items)))
        else:
            return []

    # 2. FILTER & SCORE (Limited to candidates)
    indices_list = list(candidate_indices)
    if not is_all_brand:
        # Strictly filter down to the selected brand
        indices_list = [idx for idx in indices_list if _item_brand(stored_items[idx]) == brand_lower]
        if not indices_list:
            return []
    else:
        indices_list = [idx for idx in indices_list]

    # STRICT MODE: code/model queries should resolve to one most-accurate hit.
    if is_code_query:
        query_code = strict_query_compact
        query_is_numeric = query_code.isdigit()
        query_code_relaxed = _code_relaxed(query_code)
        strict_scores = {}
        for idx in indices_list:
            item = stored_items[idx]
            item_code_meta = _get_item_code_metadata(item)
            name_lower = str(item.get("name") or "").lower()
            text_lower = str(item.get("text") or "").lower()
            # Restrict strict matching to header lines before "MRP" to avoid price-number noise.
            header_lines = []
            for raw_line in text_lower.split("\n"):
                line = raw_line.strip()
                if not line:
                    continue
                if "mrp" in line:
                    break
                header_lines.append(line)
                if len(header_lines) >= 6:
                    break
            if not header_lines:
                header_lines = [ln.strip() for ln in text_lower.split("\n")[:3] if ln.strip()]

            blob = f"{name_lower}\n" + "\n".join(header_lines)
            token_compacts = []
            for tok in _extract_model_tokens(blob):
                tok_compact = _compact_alnum(tok)
                if len(tok_compact) >= 3:
                    token_compacts.append(tok_compact)
            best = 0.0
            quality_bonus = _item_quality_bonus(item)

            # If the query points at a specific base code, keep strict matching
            # inside that family so combo products like "1334 BG + 1333" do not
            # leak into a plain "1333" search.
            if query_base_compact and item_code_meta.get("base_compact") not in {query_base_compact, ""}:
                item_base_compact = item_code_meta.get("base_compact", "")
                if item_base_compact.endswith(query_base_compact):
                    pass
                elif not (
                    query_full_compact
                    and item_code_meta.get("full_compact") == query_full_compact
                ):
                    continue

            if query_full_compact and item_code_meta.get("full_compact"):
                item_full_compact = item_code_meta["full_compact"]
                if item_full_compact == query_full_compact:
                    best = max(best, 3700.0 + quality_bonus)
                elif _code_relaxed(item_full_compact) == _code_relaxed(query_full_compact):
                    best = max(best, 3620.0 + quality_bonus)

            if query_base_compact and item_code_meta.get("base_compact") == query_base_compact:
                if query_variant_compact:
                    if item_code_meta.get("variant_compact") == query_variant_compact:
                        best = max(best, 3520.0 + quality_bonus)
                    elif item_code_meta.get("variant_compact"):
                        best = max(best, 2380.0 + quality_bonus)
                    else:
                        best = max(best, 2250.0 + quality_bonus)
                else:
                    best = max(best, 3040.0 + quality_bonus)

            # Highest confidence: exact compact token equality (with OCR-tolerant equivalent).
            has_exact_code = any(
                (tok_compact == query_code) or (_code_relaxed(tok_compact) == query_code_relaxed)
                for tok_compact in token_compacts
            )
            if has_exact_code:
                line_exact = any(_compact_alnum(line) == query_code for line in header_lines[:4])
                best = max(best, 3000.0 + (80.0 if line_exact else 0.0) + quality_bonus)
            
            # Smart Partial Logic: If query matches start of a token (e.g. "K-277" matches "K-27792IN")
            # give it a mid-range score so it appears above generic fuzzy hits.
            if best < 2500 and len(query_code) >= 4:
                prefix_match = any(tok_compact.startswith(query_code) for tok_compact in token_compacts)
                if prefix_match:
                    best = max(best, 2400.0 + quality_bonus)
            elif best < 2000 and len(query_code) >= 3:
                # Shorter prefix match also gets a boost over totally unrelated items
                prefix_match = any(tok_compact.startswith(query_code) for tok_compact in token_compacts)
                if prefix_match:
                    best = max(best, 1900.0 + quality_bonus)

            if best == 0 and query_is_numeric:
                # Numeric-only search: allow exact numeric segment only (not broad substring).
                seg_match = False
                for tok_compact in token_compacts:
                    segments = re.findall(r'\d{3,}', tok_compact)
                    if query_code in segments:
                        seg_match = True
                        break
                if seg_match:
                    line_has = any(re.search(rf'(^|\D){re.escape(query_code)}(\D|$)', line) for line in header_lines[:4])
                    best = max(best, 1700.0 + (60.0 if line_has else 0.0) + quality_bonus)

            if best > 0:
                strict_scores[idx] = best

        if strict_scores:
            ranked_strict = sorted(strict_scores.items(), key=lambda x: (-x[1], x[0]))

            # Find all products that share the exact top score
            top_score = ranked_strict[0][1]
            top_candidates = [stored_items[idx] for idx, score in ranked_strict if score == top_score]

            # PERMANENT SOLUTION: We only want ONE accurate, primary product block for a given code.
            # If the parser split things weirdly, we remove duplicate variations of the EXACT same item name.
            unique_candidates = []
            seen_names = set()
            for cand in top_candidates:
                # Use a simplified name to check for duplicates
                cand_name = re.sub(r'[^a-zA-Z0-9]', '', cand.get("name", "").lower())
                if cand_name not in seen_names:
                    seen_names.add(cand_name)
                    unique_candidates.append(cand)

            # INCREASED: Show more variants (e.g. all 12+ finishes for a code)
            max_exact_results = 15
            results = unique_candidates[:max_exact_results]
            
            search_cache[cache_key] = results
            return results
        
        # PERMANENT: If the algorithm proved it's a code search ("7512 OG", "1186 RG") and we didn't
        # hit perfectly exact above, we fall through to fuzzy but we MUST limit it to a reasonable set, 
        # so it doesn't give you random irrelevant stuff but still shows variants.
        fuzzy_max = 12
    else:
        # For non-code queries (like "wash basin", "olive green"), allow more results 
        # so user can see options, but cap to a reasonable number.
        fuzzy_max = 30

    scores = {}
    
    for idx in indices_list:
        item = stored_items[idx]
        item_code_meta = _get_item_code_metadata(item)
        name_lower = str(item.get("name") or "").lower()
        text_lower = str(item.get("text") or "").lower()
        combined = f"{name_lower}\n{text_lower}"
        first_line = text_lower.split('\n')[0] if text_lower else ""
        s = 0.0
        
        # Priority 1: Normalized match (best for model/code)
        if len(query_norm) >= 3:
            combined_norm = _normalize(combined, strip_in=query_has_digits)
            if query_norm in combined_norm:
                s += 550.0

        # Priority 2: Exact model token match
        if query_model_tokens:
            combined_code_norm = _normalize(combined, strip_in=True)
            for tok in query_model_tokens:
                tok_norm = _normalize(tok, strip_in=True)
                if tok in combined:
                    s += 300.0
                elif len(tok_norm) >= 3 and tok_norm in combined_code_norm:
                    s += 280.0

        if query_base_compact and item_code_meta.get("base_compact") == query_base_compact:
            s += 260.0
        if query_full_compact and item_code_meta.get("full_compact") == query_full_compact:
            s += 520.0
        if query_variant_compact:
            item_variant_compact = item_code_meta.get("variant_compact")
            if item_variant_compact == query_variant_compact:
                s += 340.0
            elif item_variant_compact:
                s -= 180.0

        # Priority 3: Name / first-line / text relevance
        if query_lower in name_lower:
            s += 380.0
        if query_lower in first_line:
            s += 300.0
        elif query_lower in text_lower:
            s += 120.0
        
        # Word overlap
        for w in query_words:
            if w in combined:
                s += 45.0
                if w in name_lower or w in first_line:
                    s += 35.0

        # Bonus when every query token is present.
        if query_words and all(w in combined for w in query_words):
            s += 140.0

        s += _item_quality_bonus(item)

        if s > 0:
            scores[idx] = s

    # 3. SEMANTIC BOOST (Optional & Skipped for codes)
    is_mostly_digits = len(re.findall(r'\d', query)) > len(re.findall(r'[a-zA-Z]', query))
    if smart and AI_AVAILABLE and FAISS_AVAILABLE and vector_index is not None and not is_mostly_digits:
        try:
            q_emb = model.encode([query], convert_to_numpy=True, show_progress_bar=False)
            q_emb = q_emb.astype(np.float32)
            faiss.normalize_L2(q_emb)
            k = min(100, vector_index.ntotal)
            D, I = vector_index.search(q_emb, k)
            for dist, s_idx in zip(D[0], I[0]):
                if s_idx >= 0 and dist > 0.4:
                    if is_all_brand or brand_lower == _item_brand(stored_items[s_idx]):
                        scores[s_idx] = scores.get(s_idx, 0) + float(dist) * 150.0
        except Exception: pass

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Filter out weak scores (require 400+ for code matches, 350+ for texts)
    min_score = 400 if is_code_query else 350
    
    # Filter and validate items before slicing
    filtered_items = []
    for idx, score in ranked:
        if score < min_score:
            continue
            
        item = stored_items[idx]
        
        # If the user typed a specific code modifier like "OG" or "RG", drop results that clearly don't have it
        if is_code_query and len(query_words) > 1:
            item_text_lower = (item.get("name", "") + " " + item.get("text", "")).lower()
            missing_modifier = False
            for w in query_words:
                if not w.isdigit() and len(w) <= 3:
                    # Look for the color modifier surrounded by non-alphanumeric chars or start/end of string
                    pattern = r'(?:^|[^a-zA-Z0-9])' + re.escape(w) + r'(?:[^a-zA-Z0-9]|$)'
                    if not re.search(pattern, item_text_lower):
                        missing_modifier = True
                        break
            if missing_modifier:
                continue

        filtered_items.append((item, score))

    if is_code_query and query_variant_compact:
        exact_variant_items = []
        for item, score in filtered_items:
            item_code_meta = _get_item_code_metadata(item)
            if (
                item_code_meta.get("variant_compact") == query_variant_compact
                or item_code_meta.get("full_compact") == query_full_compact
            ):
                exact_variant_items.append((item, score))
        if exact_variant_items:
            filtered_items = exact_variant_items
        
    max_results = fuzzy_max

    if is_all_brand and not is_code_query:
        # Keep "all brands" balanced, so both PDFs are visible when both have matches.
        buckets = {}
        for item, score in filtered_items:
            b = _item_brand(item) or "generic"
            buckets.setdefault(b, []).append(item)

        ordered_brands = [b for b in ("aquant", "kohler", "plumber") if b in buckets]
        ordered_brands.extend([b for b in buckets.keys() if b not in ordered_brands])

        mixed_items = []
        while len(mixed_items) < max_results:
            progressed = False
            for b in ordered_brands:
                if buckets[b]:
                    mixed_items.append(buckets[b].pop(0))
                    progressed = True
                    if len(mixed_items) >= max_results:
                        break
            if not progressed:
                break
        results = mixed_items
    else:
        results = [item for item, score in filtered_items[:max_results]]

    # Deduplicate purely by base name to avoid multiple identical images cluttering
    unique_res = []
    seen = set()
    for item in results:
        base_name = re.sub(r'[^a-zA-Z0-9]', '', item.get("name", "").lower())
        if base_name not in seen:
            seen.add(base_name)
            unique_res.append(item)
            if len(unique_res) >= max_results:
                break

    search_cache[cache_key] = unique_res
    return unique_res


def search_exact(query: str, smart: bool = False, brand: str = None):
    query = (query or "").strip()
    if not query:
        return []

    load_index()
    if not stored_items:
        return []

    brand_lower = (brand or "").strip().lower()
    if brand_lower and brand_lower != "all":
        target_brands = [brand_lower]
    else:
        target_brands = [b for b in ("aquant", "kohler", "plumber") if any(_item_brand(item) == b for item in stored_items)]
        if not target_brands:
            target_brands = [""]

    query_is_code = _is_code_or_model_query(query)
    results = []

    for target_brand in target_brands:
        best_exact_item = None
        best_exact_score = 0.0

        if not query_is_code:
            for item in stored_items:
                item_brand = _item_brand(item)
                if target_brand and item_brand != target_brand:
                    continue
                score = _exact_name_score(item, query)
                if score > best_exact_score:
                    best_exact_score = score
                    best_exact_item = item

        if best_exact_item is not None:
            results.append(best_exact_item)
            continue

        fallback = search(query, smart=smart, brand=(target_brand or None))
        if fallback:
            results.append(fallback[0])

    unique_res = []
    seen = set()
    for item in results:
        dedupe_key = f"{_item_brand(item)}|{_compact_alnum(item.get('name', ''))}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        unique_res.append(item)

    return unique_res


def _items_to_suggestion_payload(items, limit: int = 50):
    final_results = []
    seen = set()
    for item in items:
        name = str(item.get("name") or "").strip()
        if not name:
            continue

        item_code_meta = _get_item_code_metadata(item)
        parts = name.split(" - ", 1)
        code = parts[0].strip() or item_code_meta.get("full_code") or name
        description = parts[1].strip() if len(parts) > 1 else ""
        full_name = name
        dedupe_key = f"{str(item.get('brand') or '').lower()}|{full_name.lower()}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        final_results.append({
            "text": code,
            "description": description,
            "full_name": full_name,
            "brand": item.get("brand", "Aquant"),
            "image": _best_item_image(item),
            "raw_item": item,
        })
        if len(final_results) >= limit:
            break
    return final_results


def _merge_suggestion_payloads(*payload_groups, limit: int = 50):
    merged = []
    seen = set()
    for group in payload_groups:
        for item in group or []:
            key = f"{str(item.get('brand') or '').lower()}|{str(item.get('full_name') or item.get('text') or '').lower()}"
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
            if len(merged) >= limit:
                return merged
    return merged


def get_suggestions(query: str, limit: int = 50, brand: str = None):
    if not query or len(query.strip()) < 2:
        return []

    # Start model loading in background if it's the first search
    ensure_model_loaded()

    load_index()
    if not stored_items:
        return []

    # Seed suggestions from the richer search ranking first so exact and near-exact
    # product hits are available before we fall back to lightweight prefix scans.
    seeded_items = search(query, smart=False, brand=brand)
    seeded_payload = _items_to_suggestion_payload(seeded_items, limit=limit)
    query_code_meta = _parse_code_metadata(query)

    query_is_code = _is_code_or_model_query(query)
    exact_family_payload = []
    if query_is_code and (query_code_meta.get("full_compact") or query_code_meta.get("base_compact")):
        brand_lower = (brand or "").strip().lower()
        is_all_brand = (not brand_lower) or (brand_lower == "all")
        exact_family_items = []
        for item in stored_items:
            if not is_all_brand and _item_brand(item) != brand_lower:
                continue
            item_code_meta = _get_item_code_metadata(item)
            if query_code_meta.get("full_compact") and item_code_meta.get("full_compact") == query_code_meta["full_compact"]:
                exact_family_items.append(item)
                continue
            if (
                query_code_meta.get("base_compact")
                and item_code_meta.get("base_compact") == query_code_meta["base_compact"]
                and (
                    not query_code_meta.get("variant_compact")
                    or item_code_meta.get("variant_compact") == query_code_meta["variant_compact"]
                )
            ):
                exact_family_items.append(item)
        exact_family_payload = _items_to_suggestion_payload(exact_family_items, limit=limit)

    if query_is_code:
        exact_first = _merge_suggestion_payloads(exact_family_payload, seeded_payload, limit=limit)
        if exact_first:
            return exact_first

    q = query.strip().lower()
    q_compact = _compact_alnum(q)
    # Split query into words but preserve codes like K-1234
    q_words = [w for w in re.split(r'\s+', q) if len(w) >= 2]
    # Add compacted components (k282, 1234) for better lookups
    tokens_to_check = set(q_words) | {q_compact}
    if len(q_compact) > 3:
        tokens_to_check.add(q_compact[:4])
    
    # Fast retrieval using keyword index
    potential_indices = set()
    for w in tokens_to_check:
        if not w or len(w) < 2: continue
        # Normalize search token (remove dash for code prefix checks)
        wn = _normalize(w, strip_in=True)
        # Check for prefix matches in our keyword index
        for key in keyword_index:
            if key.startswith(wn) or (len(wn) >= 3 and wn in key):
                potential_indices.update(keyword_index[key])
            if len(potential_indices) > 600: break
        if len(potential_indices) > 600: break

    suggestions = []
    seen = set()
    for seeded in seeded_payload:
        seen.add(
            f"{str(seeded.get('brand') or '').lower()}|{str(seeded.get('full_name') or seeded.get('text') or '').lower()}"
        )

    brand_lower = (brand or "").strip().lower()
    is_all_brand = (not brand_lower) or (brand_lower == "all")

    # Also index with the full query as a compact token for direct matching
    q_compact = _compact_alnum(q)

    # Score and rank candidates
    for idx in potential_indices:
        item = stored_items[idx]
        
        if not is_all_brand:
            if _item_brand(item) != brand_lower:
                continue

        name = item.get("name", "")
        if not name: continue
        item_code_meta = _get_item_code_metadata(item)
        
        name_lower = name.lower()
        name_compact = _compact_alnum(name)
        
        # Simple scoring
        score = 0
        if q in name_lower: score += 10
        if any(w in name_lower for w in q_words): score += 5
        if query_code_meta.get("base_compact") and item_code_meta.get("base_compact") == query_code_meta["base_compact"]:
            score += 30
        if query_code_meta.get("full_compact") and item_code_meta.get("full_compact") == query_code_meta["full_compact"]:
            score += 150 # Significantly boost exact code matches in suggestions
        if query_code_meta.get("variant_compact"):
            if item_code_meta.get("variant_compact") == query_code_meta["variant_compact"]:
                score += 25
            elif item_code_meta.get("variant_compact"):
                score -= 10

        # Boost items where the full query string appears in name (e.g. "450-1003" in "450-1003 G - Gold")
        if len(q) >= 3 and q in name_lower:
            score += 200
        # Also boost if query compact matches the start of item name compact
        if q_compact and len(q_compact) >= 3 and name_compact.startswith(q_compact):
            score += 250

        if item.get("source") == "Manual Entry":
            score += 2000 # Massive boost
            
        if item.get("brand") in {"Aquant", "Kohler"}:
            score += 1000 # Extreme boost for core brands
            
        score += _item_quality_bonus(item)
        
        # Use item name for display to preserve prefixes like "450-" that code parsing might separate
        name_parts = name.split(" - ", 1)
        display_text = _clean_display_text(name_parts[0].strip())
        if not display_text:
            display_text = _clean_display_text(item_code_meta.get("full_code") or name.split(" - ")[0].strip())
        full_display = _clean_display_text(name.strip())
        if not display_text: continue
        
        key = f"{str(item.get('brand') or '').lower()}|{full_display.lower()}"
        entry = {
            "score": score,
            "code": display_text,
            "full_name": full_display,
            "brand": item.get("brand", "Aquant"),
            "image_list": item.get("images", []),
            "item": item
        }
        if key not in seen:
            suggestions.append(entry)
            seen.add(key)
        else:
            for i, existing in enumerate(suggestions):
                existing_key = f"{str(existing.get('brand') or '').lower()}|{str(existing.get('full_name') or '').lower()}"
                if existing_key == key and score > existing.get("score", 0):
                    suggestions[i] = entry
                    break
        
        if len(suggestions) > max(80, limit * 3):
            break

    # Sort by score descending and then by full text length
    suggestions.sort(key=lambda x: (-x["score"], len(x["full_name"])))
    
    final_results = _merge_suggestion_payloads(seeded_payload, limit=limit)
    for s in suggestions:
        if len(final_results) >= limit:
            break
        full_name = s["full_name"]
        parts = full_name.split(" - ", 1)
        name_desc = _clean_display_text(parts[1].strip()) if len(parts) > 1 else ""

        final_results.append({
            "text": _clean_display_text(s["code"]),
            "description": name_desc,
            "full_name": _clean_display_text(full_name),
            "brand": s["brand"],
            "image": _best_item_image(s["item"]),
            "raw_item": s["item"]
        })

    return final_results
