import fitz
import os

pdf_path = r'c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\uploads\Aquant Price List Vol. 14 Feb. 2025 - Low Res Searchable.pdf'
doc = fitz.open(pdf_path)

for i in range(3, 10):
    print(f"--- PAGE {i+1} ---")
    page = doc[i]
    text = page.get_text()
    print(text[:1000])
    print("-" * 20)
