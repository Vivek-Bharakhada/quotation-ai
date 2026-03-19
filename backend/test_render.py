import fitz
import os

doc = fitz.open('uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf')
page = doc[5] # page 6

# Find image 11 from my previous analysis
# xref=68, CX=513, CY=592, W=99, H=262
# Let's get all images and find xref 68
imgs = page.get_images(full=True)
for i, img_info in enumerate(imgs):
    xref = img_info[0]
    if xref == 68 or i == 5: # Just check a few
        rects = page.get_image_rects(xref)
        if rects:
            r = rects[0]
            # Use get_pixmap with clip to get exactly what's on the page
            pix = page.get_pixmap(clip=r, dpi=150)
            fname = f'static/images/test_crop_i{i}_x{xref}.jpg'
            pix.save(fname)
            print(f'Saved rendered crop for {xref} at {fname} ({pix.width}x{pix.height})')

# Let's also do it for all "large" images on page 6
for i, img_info in enumerate(imgs):
    xref = img_info[0]
    rects = page.get_image_rects(xref)
    if rects:
        r = rects[0]
        if r.width > 50 and r.height > 50:
            pix = page.get_pixmap(clip=r, dpi=150)
            fname = f'static/images/p6_render_{i}.jpg'
            pix.save(fname)
            print(f'Rendered {i} at {fname}')
