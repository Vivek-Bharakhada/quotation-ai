import os, fitz
files = [f for f in os.listdir('uploads') if 'Aquant' in f and f.endswith('.pdf')]
path = os.path.join('uploads', files[0])
doc = fitz.open(path)
page = doc[3] # Page 4
print(f"Page 4 Products count: ...")
for img in page.get_images():
    xref = img[0]
    rects = page.get_image_rects(xref)
    print(f"Xref: {xref}, Rects: {rects}")
doc.close()
