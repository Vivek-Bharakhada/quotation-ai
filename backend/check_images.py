import json, os

data = json.load(open('search_index_v2.json', encoding='utf-8'))
items = data['stored_items']

img_dir = os.path.join('static', 'images')
results = {'missing': 0, 'tiny': 0, 'cover': 0, 'ok': 0, 'no_img': 0}
brand_stats = {}

for item in items:
    src = item.get('source', '').lower()
    brand = 'aquant' if 'aquant' in src else ('kohler' if 'kohler' in src else 'plumber')
    imgs = item.get('images', [])
    if not imgs:
        results['no_img'] += 1
        continue
    for img in imgs:
        fname = img.replace('/static/images/', '')
        full = os.path.join(img_dir, fname)
        if not os.path.exists(full):
            results['missing'] += 1
        else:
            sz = os.path.getsize(full)
            if sz < 8000:
                results['tiny'] += 1
                brand_stats.setdefault(brand, {'tiny': 0, 'cover': 0})
                brand_stats[brand]['tiny'] += 1
            elif '_p0_' in img or (brand != 'aquant' and '_p1_' in img):
                results['cover'] += 1
                brand_stats.setdefault(brand, {'tiny': 0, 'cover': 0})
                brand_stats[brand]['cover'] += 1
            else:
                results['ok'] += 1

print('Image stats:')
for k, v in results.items():
    print('  ' + k + ': ' + str(v))
print()
print('Brand breakdown (bad images):')
for b, s in brand_stats.items():
    print('  ' + b + ': tiny=' + str(s.get('tiny', 0)) + ', cover=' + str(s.get('cover', 0)))
