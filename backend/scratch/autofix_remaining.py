"""
Fix remaining 10 price=0 items by targeted PDF search
"""
import json, sys, os, re, pdfplumber
sys.stdout.reconfigure(encoding='utf-8')

INDEX_PATH  = r'C:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json'
AQUANT_PDF  = r'C:\Movies\quotation-ai\quotation-ai\backend\uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf'
KOHLER_PDF  = os.path.join(r'C:\Movies\quotation-ai\quotation-ai\backend\uploads', "Kohler_Pricebook (March'26).pdf")

with open(INDEX_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
stored = data['stored_items']

# Remaining items to fix
targets = {
    'Aquant': ['11333', '2031', '7512', '1785'],
    'Kohler': ['K-33979IN-4', 'K-33979IN', 'K-45432IN', 'K-20746IN']
}

def search_pdf(pdf_path, keywords):
    """Search PDF pages for each keyword, return {keyword: price}"""
    results = {}
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue
            for kw in keywords:
                if kw in text:
                    lines = text.split('\n')
                    for j, line in enumerate(lines):
                        if kw in line:
                            # Search this line and next 3 lines for price
                            search_block = '\n'.join(lines[j:j+4])
                            pm = re.search(r'(?:MRP[^\d]*|`\s*|Rs\.?\s*)(\d[\d,]+)', search_block)
                            if pm:
                                price = pm.group(1).replace(',','')
                                if kw not in results:
                                    results[kw] = price
                                    print(f"  Found: {kw} → ₹{price} (page {i+1})")
    return results

print("Searching Aquant PDF for remaining items...")
aquant_results = search_pdf(AQUANT_PDF, ['11333', '2031', '7512', '1785'])

print("\nSearching Kohler PDF for remaining items...")
kohler_results = search_pdf(KOHLER_PDF, ['33979IN', '45432IN', '20746IN'])

# Apply fixes
fix_count = 0
for i, item in enumerate(stored):
    price = str(item.get('price','0')).strip()
    if price not in ['0','','None','null','0.0']:
        continue

    code = (item.get('search_code') or item.get('base_code') or '').strip()
    brand = item.get('brand','')

    found_price = None

    if brand == 'Aquant':
        for kw, p in aquant_results.items():
            if kw in code:
                found_price = p
                break

    elif brand == 'Kohler':
        for kw, p in kohler_results.items():
            if kw in code.replace(' ','').replace('-','') or kw.replace('IN','IN-') in code:
                found_price = p
                break
        # Also try direct match
        for kw, p in kohler_results.items():
            base = kw.replace('IN','').replace('-','')
            if base in code.replace('-','').replace(' ',''):
                found_price = p
                break

    if found_price:
        stored[i]['price'] = found_price
        fix_count += 1
        print(f"  ✅ [{i:04d}] {code} → ₹{found_price}")

print(f"\nFixed: {fix_count}")

# Final check
still_zero = [(i,it) for i,it in enumerate(stored)
              if str(it.get('price','0')).strip() in ['0','','None','null','0.0']]
print(f"Still price=0: {len(still_zero)}")
for i,it in still_zero:
    print(f"  [{i:04d}] [{it.get('brand')}] {it.get('search_code') or it.get('base_code')}")

# Save
with open(INDEX_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print("\n✅ Saved!")
