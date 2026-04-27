import fitz
import sys

pdf_path = "uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
doc = fitz.open(pdf_path)
page = doc[14] # Page 15 (0-indexed)
text = page.get_text()
print(text)
