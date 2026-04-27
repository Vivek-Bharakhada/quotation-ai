import fitz

pdf_path = "uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
doc = fitz.open(pdf_path)

for i, page in enumerate(doc):
    text = page.get_text()
    if "1333" in text and "MRP" in text:
        print(f"Page {i}:")
        lines = text.splitlines()
        for j, line in enumerate(lines):
            if "1333" in line or "MRP" in line:
                print(f"  {line}")
        print("-" * 20)
