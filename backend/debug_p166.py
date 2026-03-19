import fitz, os
doc = fitz.open('uploads/Kohler_Pricebook (March\'26).pdf')
page = doc[165]
res = []
for b in page.get_text('blocks'):
    t = b[4].strip()
    if t:
        cx, cy = (b[0]+b[2])/2, (b[1]+b[3])/2
        res.append(f'T CX={cx:.0f}, CY={cy:.0f} | {t.replace("\n", " ")[:60]}')
for i, img in enumerate(page.get_images(full=True)):
    rects = page.get_image_rects(img[0])
    if rects:
        r = rects[0]
        cx, cy = (r.x0+r.x1)/2, (r.y0+r.y1)/2
        res.append(f'I {i}: CX={cx:.0f}, CY={cy:.0f}, W={r.width:.0f}, H={r.height:.0f}')
with open('p166_layout.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(res))
