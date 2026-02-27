import os
import json
from pdf_reader import extract_content

pdf_path = os.path.join("uploads", "Aquant Price List Vol. 14 Feb. 2025 - Low Res Searchable.pdf")
print(f"Extracting {pdf_path}")
content = extract_content(pdf_path)

# Print first 20 items where Aquant is mentioned
for i, item in enumerate(content):
    if len(item["text"]) < 50: continue
    print("--- ITEM ---")
    print(f"Page: {item['page']}")
    print(f"Images: {item['images']}")
    print(item["text"])
    print("-" * 20)
    if i > 50:
        break
