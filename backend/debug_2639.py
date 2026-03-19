import fitz, os, io
from PIL import Image

doc = fitz.open('uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf')
page = doc[5]

blocks = page.get_text('blocks')
sorted_blocks = sorted(blocks, key=lambda b: b[1])
result_lines = []
for b in sorted_blocks:
    text = b[4].replace('\n', ' ').strip()
    cx = (b[0] + b[2]) / 2
    cy = (b[1] + b[3]) / 2
    if text:
        result_lines.append(f'CX={cx:.0f}, CY={cy:.0f} | "{text[:70]}"')

imgs = page.get_images(full=True)
img_rects = []
for i, img in enumerate(imgs):
    rects = page.get_image_rects(img[0])
    if rects:
        r = rects[0]
        if r.width > 30 and r.height > 30:
            cx = (r.x0 + r.x1) / 2
            cy = (r.y0 + r.y1) / 2
            img_rects.append((cy, i, img[0], cx, cy, r.width, r.height))

with open('debug_2639_output.txt', 'w', encoding='utf-8') as f:
    f.write('=== TEXT BLOCKS ===\n')
    for l in result_lines:
        f.write(l + '\n')
    f.write('\n=== IMAGES ===\n')
    for cy, i, xref, cx, _, w, h in sorted(img_rects):
        f.write(f'Image {i}: xref={xref} CX={cx:.0f}, CY={cy:.0f}, W={w:.0f}, H={h:.0f}\n')

print('Written to debug_2639_output.txt')
