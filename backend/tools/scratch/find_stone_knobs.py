import fitz

pdf_path = "uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
doc = fitz.open(pdf_path)

for i, page in enumerate(doc):
    text = page.get_text()
    if "Stone Knobs" in text:
        print(f"Page {i}:")
        print(text)
        print("-" * 20)
