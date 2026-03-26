import os
import fitz
from PIL import Image

pdf_path = r"uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
doc = fitz.open(pdf_path)
page = doc[7]  # Page 8

# Get all images on page
images = page.get_images(full=True)
print(f"Total images on page 8: {len(images)}")

output_dir = "debug_page8_images"
os.makedirs(output_dir, exist_ok=True)

# Anchors from pdf_reader.py (my fixed ones)
anchors = {
    "1961SET_AB": (103.0, 110.0),
    "1961SET_G": (103.0, 303.0),
    "1962SET_AB": (297.0, 111.0),
    "1962SET_G": (297.0, 304.0),
}

for name, (ax, ay) in anchors.items():
    best_img = None
    min_dist = 999999
    
    for img_info in images:
        xref = img_info[0]
        rects = page.get_image_rects(xref)
        for rect in rects:
            cx = (rect.x0 + rect.x1) / 2
            cy = (rect.y0 + rect.y1) / 2
            dist = ((cx - ax)**2 + (cy - ay)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                best_img = (xref, rect)
    
    if best_img:
        xref, rect = best_img
        pix = doc.extract_image(xref)
        with open(os.path.join(output_dir, f"{name}.{pix['ext']}"), "wb") as f:
            f.write(pix["image"])
        print(f"Saved {name} (dist={min_dist:.1f})")
