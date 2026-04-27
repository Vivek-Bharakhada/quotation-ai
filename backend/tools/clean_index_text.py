import json
import re

INDEX_PATH = "search_index_v2.json"

def clean_text(text: str) -> str:
    if not text:
        return ""
    s = str(text)
    replacements = {
        "â€¢": "•",
        "â€“": "–",
        "â€”": "—",
        "Ã¢-žÂ¢": "™",
        "Ã¢â‚¬â„¢": "'",
        "Ã¢â‚¬": "-",
        "â€™": "'",
        "â€œ": '"',
        "â€?": '"',
        "â–": "•",
        "â–=": "•",
        "â\x9e¢": "™",
        "â\x84¢": "™",
        "â€": "",
        "Â": "",
        "â": "",
    }
    for bad, good in replacements.items():
        s = s.replace(bad, good)
    s = re.sub(r'Ã[¢\-\sžÂ]+[¢Â]?', '™', s)
    s = s.replace("Ã", "")
    for bullet in ("•", "●", "▪", "◦", "◾", "■"):
        s = s.replace(bullet, "-")
    s = re.sub(r"\s{2,}", " ", s)
    return s.strip()

def main():
    with open(INDEX_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
        items = data.get("stored_items", [])

    print(f"Cleaning {len(items)} items...")
    
    for item in items:
        for key in ("name", "text"):
            if key in item:
                item[key] = clean_text(item[key])

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    
    print("Clean complete.")

if __name__ == "__main__":
    main()
