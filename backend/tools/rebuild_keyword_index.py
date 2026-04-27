import json
import re

INDEX_PATH = "search_index_v2.json"

def _compact_alnum(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', str(text).lower())

def _normalize(text, strip_in=False):
    t = re.sub(r'[\s\-\/\.\_\u2013\u2014]+', '', str(text).lower())
    if strip_in:
        t = t.replace('in', '')
    return t

def _code_like(text: str) -> bool:
    return bool(re.search(r'[a-z]', text.lower())) and bool(re.search(r'\d', text))

def _extract_model_tokens(text: str):
    seen = set()
    ordered = []
    # Simplified regex logic from search_engine.py
    for tok in re.findall(r'[a-z]{1,4}[-/]?\d{2,}[a-z0-9/-]*|\b\d{3,}\b', text.lower()):
        if tok not in seen:
            seen.add(tok)
            ordered.append(tok)
    return ordered

def main():
    with open(INDEX_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
        items = data.get("stored_items", [])

    print(f"Rebuilding index for {len(items)} items...")
    
    keyword_index = {}
    
    for idx, item in enumerate(items):
        text = item.get("text", "")
        name = item.get("name", "")
        search_blob = f"{name}\n{text}".strip()
        blob_lower = search_blob.lower()

        words_to_index = set()

        # 1. Broad split
        tokens = re.split(r'[\s\-\/\.\_\u2013\u2014\(\)\[\],:;]+', blob_lower)
        for w in tokens:
            w = w.strip()
            if len(w) >= 2:
                words_to_index.add(w)
                if _code_like(w):
                    words_to_index.add(_normalize(w, strip_in=True))

        # 2. Extract model/code tokens
        for model_tok in _extract_model_tokens(search_blob):
            words_to_index.add(model_tok)
            norm_tok = _normalize(model_tok, strip_in=True)
            if len(norm_tok) >= 3:
                words_to_index.add(norm_tok)

        # 3. Code segments (from search_engine.py logic)
        code_segments = re.findall(r'[a-z]{1,4}|\d{2,}', blob_lower)
        for seg in code_segments:
            if len(seg) >= 3:
                words_to_index.add(seg)

        # Add to index
        for word in words_to_index:
            if word not in keyword_index:
                keyword_index[word] = []
            keyword_index[word].append(idx)

    # Save
    data["keyword_index"] = keyword_index
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    
    print(f"Rebuild complete. Index saved.")

if __name__ == "__main__":
    main()
