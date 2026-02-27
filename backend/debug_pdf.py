import fitz, os, sys

pdf = [f for f in os.listdir('uploads') if 'aquant' in f.lower() or 'Aquant' in f][0]
doc = fitz.open(os.path.join('uploads', pdf))

out = []

for page_num in [10, 15, 20]:
    if page_num >= len(doc): continue
    page = doc[page_num]
    d = page.get_text('dict')
    lines_data = []
    for block in d.get('blocks', []):
        if block.get('type', -1) == 0:
            for line in block.get('lines', []):
                t = ''.join(s.get('text','') for s in line.get('spans',[])).replace(chr(3),' ').strip()
                if t:
                    lines_data.append((round(line['bbox'][1]), round(line['bbox'][0]), t))
    lines_data.sort()
    out.append(f'\n=== PAGE {page_num+1} ===')
    for y, x, t in lines_data:
        out.append(f'  y={y} x={x}: {t[:150]}')

with open('debug_layout.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('Written to debug_layout.txt')
print('First 100 lines:')
print('\n'.join(out[:100]))
