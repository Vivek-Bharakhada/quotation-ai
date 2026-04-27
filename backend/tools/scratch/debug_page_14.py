import fitz

pdf_path = "uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
doc = fitz.open(pdf_path)
page = doc[14]
text = page.get_text()
print(text)
# Get blocks to see position of "15"
blocks = page.get_text("blocks")
for b in blocks:
    if "1333" in b[4] or "15" in b[4]:
        print(f"Block: {b[4].strip()} at {b[:4]}")
