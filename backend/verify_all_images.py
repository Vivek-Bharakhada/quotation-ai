import os
import json

index_path = 'search_index_v2.json'
with open(index_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print('--- VERIFYING INDEX IMAGES ---')
missing_count = 0
found_count = 0
for item in data.get('stored_items', []):
    imgs = item.get('images', [])
    if imgs:
        raw_path = imgs[0]
        # Images are stored as /static/images/foo.jpg. 
        # Map to local path: static/images/foo.jpg
        local_path = raw_path.lstrip('/')
        if os.path.exists(local_path):
            found_count += 1
        else:
            missing_count += 1
            if missing_count < 10:
                print(f'MISSING: {item.get("name")} (at {local_path})')

print(f'\nTotal Found: {found_count}')
print(f'Total Missing: {missing_count}')
