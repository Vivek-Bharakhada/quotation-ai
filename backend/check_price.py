import fitz

doc = fitz.open('uploads/Plumber Bathware.pdf')
with open('plumber_pdf_pages.txt', 'w', encoding='utf-8') as f:
    for pg_no in range(min(4, len(doc))):
        page = doc[pg_no]
        f.write(f"\n\n====== PAGE {pg_no+1} ======\n")
        f.write(page.get_text())
print("Done")
