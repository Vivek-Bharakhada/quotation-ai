import fitz
doc = fitz.open("uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf")

for pg in [40, 58, 63, 64, 15, 51, 71, 85]:
    page = doc[pg - 1]
    imgs = page.get_image_info()
    blocks = page.get_text("blocks")
    print("Page %d: %d images, %d blocks" % (pg, len(imgs), len(blocks)))
    for i, img in enumerate(imgs):
        cx = int((img["bbox"][0] + img["bbox"][2]) / 2)
        cy = int((img["bbox"][1] + img["bbox"][3]) / 2)
        w = int(img["bbox"][2] - img["bbox"][0])
        h = int(img["bbox"][3] - img["bbox"][1])
        print("  Img%d cx=%d cy=%d %dx%d" % (i, cx, cy, w, h))
    # text blocks with codes
    for b in blocks:
        if b[6] != 0:
            continue
        txt = b[4].strip()[:60]
        if len(txt) > 3:
            print("  TXT y=%.0f: %s" % (b[1], txt.replace('\n', ' | ')))
    print()
