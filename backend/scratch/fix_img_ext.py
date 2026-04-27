import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

INDEX_PATH = r'C:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json'

with open(INDEX_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
stored = data['stored_items']

fixes = {
    2456: '/static/images/Kohler/K-38893IN-4ND-BV(K-38893IN-4ND-BV).png',
    2760: '/static/images/Kohler/K-38888IN-4ND-BRD(K-38888IN-4ND-BRD).png',
    2761: '/static/images/Kohler/K-38887IN-4ND-BRD(K-38887IN-4ND-BRD).png',
    2762: '/static/images/Kohler/K-38886IN-4ND-BRD(K-38886IN-4ND-BRD).png',
}

for idx, img_path in fixes.items():
    stored[idx]['images'] = [img_path]
    code = stored[idx].get('search_code', 'N/A')
    print(f'Fixed [{idx}] {code} -> {img_path}')

with open(INDEX_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print('Saved!')
