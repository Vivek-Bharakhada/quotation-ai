import fitz
import os

pdf_path = r"uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
doc = fitz.open(pdf_path)
page = doc[7]  # 0-indexed, so page 8 is index 7

# Get page images
images = page.get_images(full=True)
print(f"Total images on page 8: {len(images)}")

with open("page8_debug_out.txt", "w", encoding="utf-8") as f:
    f.write(f"Total images on page 8: {len(images)}\n")

    for img_index, img in enumerate(images):
        xref = img[0]
        image_rects = page.get_image_rects(xref)
        for rect_index, rect in enumerate(image_rects):
            f.write(f"Image {img_index} Rect {rect_index}: {rect}\n")

    blocks = page.get_text("blocks")
    for b in blocks:
        f.write(f"Block: {b[:4]} Text: {b[4].strip()}\n")
