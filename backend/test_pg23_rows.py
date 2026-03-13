import pdf_reader
import fitz
import os

pdf_path = 'uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf'
doc = fitz.open(pdf_path)
page = doc[22] # PG 23
page_num = 22

# Replicate img_records extraction from pdf_reader
img_records = []
for i, img in enumerate(page.get_images(full=True)):
    xref = img[0]
    rects = page.get_image_rects(xref)
    if rects:
        for j, rect in enumerate(rects):
            img_records.append({"xref": xref, "rect": rect, "path": f"dummy_p{page_num}_i{i}_{j}.jpg"})

# Replicate dict extraction
d = page.get_text("dict")
for i, b in enumerate(d.get("blocks", [])):
    if b.get("type") == 1:
        rect = fitz.Rect(b["bbox"])
        is_duplicate = False
        for existing in img_records:
            if rect.intersects(existing["rect"]) and rect.intersect(existing["rect"]).area > rect.area * 0.8:
                is_duplicate = True; break
        if not is_duplicate:
            img_records.append({"rect": rect, "path": f"block_p{page_num}_b{i}.jpg"})

print(f"Total img_records on pg 23: {len(img_records)}")

rows = pdf_reader.build_aquant_image_rows(img_records)
print(f"Number of rows found: {len(rows)}")
for i, row in enumerate(rows):
    print(f"Row {i}: {len(row['images'])} images at CY={row['cy']:.1f}")

# Replicate the filter
image_rows = [r for r in rows if 4 <= len(r["images"]) <= 12]
print(f"Number of rows passing 4-12 filter: {len(image_rows)}")
