import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

stored = data['stored_items']

# Fix index 3005 - Manual Entry with price 0
print('=== Entry 3005 BEFORE ===')
print(json.dumps(stored[3005], indent=2, ensure_ascii=False))

stored[3005].update({
    'name': '1D1P/1D2P ht. extn 10mm 2400mm Height Extn. (K-704703IN-2BL)',
    'text': '1D1P/1D2P ht. extn 10mm 2400mm Height Extn.\nK-704703IN-2BL\nMRP 27500\nKohler Shower Enclosure',
    'price': '27500',
    'page': 81,
    'source': "Kohler_Pricebook (March'26)",
    'brand': 'Kohler',
    'category': 'Shower Enclosures',
    'search_code': 'K-704703IN-2BL',
    'base_code': 'K-704703IN-2BL',
    'full_code': 'K-704703IN-2BL',
})
stored[3005].pop('variant_code', None)

print('\n=== Entry 3005 AFTER ===')
print(json.dumps(stored[3005], indent=2, ensure_ascii=False))

# Fix index 1521 - has correct price but search_code is wrong ("1D1P")
print('\n=== Entry 1521 BEFORE search_code ===', stored[1521].get('search_code'))
stored[1521]['search_code'] = 'K-704703IN-2BL'
stored[1521]['name'] = '1D1P/1D2P ht. extn 10mm 2400mm Height Extn. (K-704703IN-2BL)'
print('=== Entry 1521 AFTER search_code ===', stored[1521].get('search_code'))

# Save updated index
with open(r'C:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)

print('\nDone! search_index_v2.json updated successfully.')
