import numpy as np
import re
import os
import json
import threading

import cloud_storage

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Lazy model loading - loads in background to avoid blocking app startup
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
        print(f"Warning: Semantic model not available: {e}")
    finally:
        _model_loading = False

def ensure_model_loaded():
    """Trigger model loading if not already started."""
    global _model_loading
    
    # Memory workaround: The 512MB RAM limit is too small for SentenceTransformer. 
    # Detect Railway or Render to skip heavy AI model loading.
    if os.environ.get("RENDER") or os.environ.get("RAILWAY_ENVIRONMENT_NAME") or os.environ.get("RAILWAY_STATIC_URL"):
        print("--- RAILWAY/RENDER DETECTED: SKIPPING HEAVY AI MODEL TO PREVENT OOM CRASH ---")
        return

    if model is None and not _model_loading:
        _model_loading = True
        threading.Thread(target=_load_model_background, daemon=True).start()

# Start loading model in background immediately on import (non-blocking)
print("Queuing Semantic Model for background load...")
ensure_model_loaded()

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


INDEX_FILE = os.path.join(BASE_DIR, "search_index_v2.json")
SEARCH_INDEX_OBJECT_PATH = os.getenv("SUPABASE_SEARCH_INDEX_PATH", "search/search_index_v2.json")

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

def load_index():
    global stored_items, keyword_index, vector_index, search_cache, catalog_summary_cache
    if not os.path.exists(INDEX_FILE) and cloud_storage.is_enabled():
        try:
            restored = cloud_storage.download_to_path(
                cloud_storage.SYSTEM_BUCKET,
                SEARCH_INDEX_OBJECT_PATH,
                INDEX_FILE,
            )
            if restored:
                print("Restored search index from cloud storage.")
        except Exception as e:
            print(f"Warning: failed to restore index from cloud storage: {e}")

    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                stored_items = data.get("stored_items", [])
                keyword_index = data.get("keyword_index", {})
            print(f"Index loaded: {len(stored_items)} items")
            
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
    global stored_items, keyword_index, vector_index, search_cache, catalog_summary_cache
    stored_items   = []
    keyword_index  = {}
    vector_index   = None
    search_cache   = {}
    catalog_summary_cache = None
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
    tokens = re.findall(r'[a-z0-9/-]+', q)
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
        
    if not stored_items:
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

    # Prefer an explicit code-like token from the query (e.g. "kohler K-28220T-SL-0").
    strict_query_compact = ""
    for tok in query_model_tokens:
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

            # Highest confidence: exact compact token equality (with OCR-tolerant equivalent).
            has_exact_code = any(
                (tok_compact == query_code) or (_code_relaxed(tok_compact) == query_code_relaxed)
                for tok_compact in token_compacts
            )
            if has_exact_code:
                line_exact = any(_compact_alnum(line) == query_code for line in header_lines[:4])
                best = max(best, 3000.0 + (80.0 if line_exact else 0.0))

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
                    best = max(best, 1700.0 + (60.0 if line_has else 0.0))

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

            # Return at most 2 distinct variants (like 2 distinct colors), but normally just 1.
            results = unique_candidates[:2]
            
            search_cache[cache_key] = results
            return results
        
        # PERMANENT: If the algorithm proved it's a code search ("7512 OG", "1186 RG") and we didn't
        # hit perfectly exact above, we fall through to fuzzy but we MUST limit it to 1 result, 
        # so it doesn't give you random basins just because they matched "OG".
        fuzzy_max = 1
    else:
        # For non-code queries (like "wash basin", "olive green"), allow more results 
        # so user can see options, but cap to a reasonable number.
        fuzzy_max = 5

    scores = {}
    
    for idx in indices_list:
        item = stored_items[idx]
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

    if not stored_items:
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


def get_suggestions(query: str, limit: int = 10, brand: str = None):
    if not query or len(query.strip()) < 2:
        return []

    q = query.strip().lower()
    q_words = [w for w in re.split(r'[\s\-\/]+', q) if len(w) >= 2]
    if not q_words:
        return []

    # Fast retrieval using keyword index
    potential_indices = set()
    for w in q_words:
        # Check for prefix matches in our keyword index as well
        for key in keyword_index:
            if key.startswith(w):
                potential_indices.update(keyword_index[key])
            if len(potential_indices) > 500: break
        if len(potential_indices) > 500: break

    suggestions = []
    seen = set()

    brand_lower = (brand or "").strip().lower()
    is_all_brand = (not brand_lower) or (brand_lower == "all")

    # Score and rank candidates
    for idx in potential_indices:
        item = stored_items[idx]
        
        if not is_all_brand:
            if _item_brand(item) != brand_lower:
                continue

        name = item.get("name", "")
        if not name: continue
        
        name_lower = name.lower()
        
        # Simple scoring
        score = 0
        if q in name_lower: score += 10
        if any(w in name_lower for w in q_words): score += 5
        
        # Use a more descriptive text for the suggestion key
        display_text = name.split(" - ")[0].strip()
        full_display = name.strip()
        if not display_text: continue
        
        key = full_display.lower()
        if key not in seen:
            suggestions.append({
                "score": score,
                "code": display_text,
                "full_name": full_display,
                "brand": item.get("brand", "Aquant"),
                "image_list": item.get("images", [])
            })
            seen.add(key)
        
        if len(suggestions) > 50: break

    # Sort by score descending and then by full text length
    suggestions.sort(key=lambda x: (-x["score"], len(x["full_name"])))
    
    final_results = []
    for s in suggestions[:limit]:
        full_name = s["full_name"]
        parts = full_name.split(" - ", 1)
        code = parts[0].strip()
        name_desc = parts[1].strip() if len(parts) > 1 else ""
        
        final_results.append({
            "text": code,
            "description": name_desc,
            "brand": s["brand"],
            "image": s["image_list"][0] if s["image_list"] else None
        })
        
    return final_results

