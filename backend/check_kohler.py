import json, os
data = json.load(open('search_index_v2.json', encoding='utf-8'))
items = data['stored_items']

# Find a small Kohler image and view it
sample = None
for item in items:
    if 'kohler' not in item.get('source','').lower():
        continue
    imgs = item.get('images', [])
    for img in imgs:
        full = os.path.join('static', 'images', os.path.basename(img))
        if os.path.exists(full):
            sz = os.path.getsize(full)
            if 4000 < sz < 7000:
                sample = (item.get('name',''), img, sz)
                break
    if sample:
        break

if sample:
    name, img, sz = sample
    print('Name:', name[:60])
    print('Img:', os.path.basename(img), '(' + str(sz) + ' bytes)')
