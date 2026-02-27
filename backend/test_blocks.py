import fitz

pdf_path = r'c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\uploads\Aquant Price List Vol. 14 Feb. 2025 - Low Res Searchable.pdf'
doc = fitz.open(pdf_path)
page = doc[3]

for b in page.get_text("blocks")[:15]:
    text = b[4].strip()
    if text:
        print(f"BLOCK {b[:4]}:\n{text}\n--")
