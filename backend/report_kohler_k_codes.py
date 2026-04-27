import csv
import json
import os
from collections import Counter, defaultdict


BASE_DIR = os.path.dirname(__file__)
INDEX_PATH = os.path.join(BASE_DIR, "search_index_v2.json")
DUPLICATES_PATH = os.path.join(BASE_DIR, "kohler_k_code_duplicates.csv")
CATEGORY_PATH = os.path.join(BASE_DIR, "kohler_k_code_categories.csv")


def main():
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("stored_items", []) if isinstance(data, dict) else data

    code_counts = Counter()
    code_examples = defaultdict(list)
    category_counts = Counter()

    for item in items:
        if str(item.get("brand", "")).strip().lower() != "kohler":
            continue
        name = str(item.get("name", "")).strip()
        if not name.upper().startswith("K-"):
            continue
        code = name.split(" - ", 1)[0].strip()
        code_counts[code] += 1
        if len(code_examples[code]) < 3:
            code_examples[code].append(name)
        category = str(item.get("category", "")).strip() or "Uncategorized"
        category_counts[category] += 1

    with open(DUPLICATES_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "occurrences", "example_names"])
        for code, count in code_counts.most_common():
            if count <= 1:
                continue
            writer.writerow([code, count, " | ".join(code_examples[code])])

    with open(CATEGORY_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "count"])
        for category, count in category_counts.most_common():
            writer.writerow([category, count])

    print(f"Duplicate report written: {DUPLICATES_PATH}")
    print(f"Category report written: {CATEGORY_PATH}")
    print(f"Unique K codes: {len(code_counts)}")
    print(f"Duplicate codes: {sum(1 for count in code_counts.values() if count > 1)}")


if __name__ == "__main__":
    main()
