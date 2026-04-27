import search_engine
import re

search_engine.load_index()
query = "7008"
query_code = "7008"
query_code_relaxed = "7008"

found = 0
for idx, item in enumerate(search_engine.stored_items):
    name = item.get("name", "")
    if "7008" not in name: continue
    
    found += 1
    name_lower = name.lower()
    text_lower = str(item.get("text", "")).lower()
    header_lines = [ln.strip() for ln in text_lower.split("\n")[:3] if ln.strip()]
    blob = f"{name_lower}\n" + "\n".join(header_lines)
    
    token_compacts = []
    for tok in search_engine._extract_model_tokens(blob):
        tok_compact = search_engine._compact_alnum(tok)
        if len(tok_compact) >= 3:
            token_compacts.append(tok_compact)
    
    prefix_match = any(tok_compact.startswith(query_code) for tok_compact in token_compacts)
    print(f"Item: {name}, Tokens: {token_compacts}, Prefix Match: {prefix_match}")

print(f"Total with 7008 in name: {found}")
