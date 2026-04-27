import fitz

pdf_path = "uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
doc = fitz.open(pdf_path)
page = doc[14]
blocks = page.get_text("blocks")
for i, b in enumerate(blocks):
    print(f"Block {i}: {b[4].strip()} at {b[:4]}")
