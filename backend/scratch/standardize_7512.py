import json

INDEX_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json"

def standardize_7512_codes():
    with open(INDEX_PATH, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    
    # Target codes as they appear in PDF
    correct_codes = {
        "7512 MI + 7514 MB + 7513 MI": "7512 MI + 7514 MB + 7513 MI",
        "7512 MG + 7514 MB + 7513 MG": "7512 MG + 7514 MB + 7513 MG",
        "7512 TCR + 7514 MB + 7513": "7512 TCR + 7514 MB + 7513 TCR", # Fixing this one
        "7512 OG + 7514 MB + 7513 OG": "7512 OG + 7514 MB + 7513 OG"
    }
    
    fixed_count = 0
    for item in data["stored_items"]:
        old_code = item.get("search_code")
        if old_code in correct_codes:
            new_code = correct_codes[old_code]
            item["search_code"] = new_code
            # Also update name to be consistent
            item["name"] = new_code
            # Ensure images are correct
            color = new_code.split(" ")[1] # e.g. MI, MG, TCR, OG
            filename = new_code.replace(" ", "") + ".png"
            item["images"] = [f"/static/images/Aquant/{filename}"]
            fixed_count += 1
            print(f"Standardized: {old_code} -> {new_code}")

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Total standardized: {fixed_count}")

if __name__ == "__main__":
    standardize_7512_codes()
