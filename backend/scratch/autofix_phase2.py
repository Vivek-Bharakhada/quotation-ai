"""
PHASE 2 AUTO-FIX:
1. Extract Aquant prices from PDF for remaining price=0 items
2. Delete garbage Kohler entries
"""
import json, sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

INDEX_PATH  = r'C:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json'
AQUANT_PDF  = r'C:\Movies\quotation-ai\quotation-ai\backend\uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf'

print("Loading index...")
with open(INDEX_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
stored = data['stored_items']
print(f"Total items: {len(stored)}")

# ============================================================
# STEP A: Build Aquant price map from PDF
# ============================================================
import pdfplumber

print("\nScanning Aquant PDF...")
aquant_price_map = {}  # base_code -> price

with pdfplumber.open(AQUANT_PDF) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        lines = text.split('\n')
        for j, line in enumerate(lines):
            # Look for numeric product codes (Aquant uses 4-digit codes like 2641, 5134)
            codes = re.findall(r'\b(\d{3,5}(?:-\d+)?(?:\s?[A-Z0-9]+)?)\b', line)
            price_match = re.search(r'(?:MRP[^\d]*|`\s*|Rs\.?\s*)(\d[\d,]+)', line)
            if not price_match:
                # Check next lines
                for k in range(1, 4):
                    if j + k < len(lines):
                        pm = re.search(r'(?:MRP[^\d]*|`\s*|Rs\.?\s*)(\d[\d,]+)', lines[j+k])
                        if pm:
                            price_match = pm
                            break
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                for code in codes:
                    code_clean = code.strip()
                    if code_clean and len(code_clean) >= 3:
                        aquant_price_map[code_clean.upper()] = price_str

print(f"Aquant price map: {len(aquant_price_map)} entries")

# ============================================================
# STEP B: Find remaining price=0 items & fix with Aquant PDF
# ============================================================
print("\n--- Fixing remaining Aquant price=0 items ---")

fix_count = 0
still_zero = []

for i, item in enumerate(stored):
    price = str(item.get('price', '0')).strip()
    if price not in ['0', '', 'None', 'null', '0.0']:
        continue
    if item.get('brand') != 'Aquant':
        still_zero.append((i, item))
        continue

    code = (item.get('search_code') or item.get('base_code') or '').strip()
    # Try exact, then base number only
    found_price = None

    candidates = [code.upper()]
    # base number (e.g. "2641 BRG" -> "2641")
    base_num = code.split(' ')[0].upper()
    candidates.append(base_num)
    # full code without spaces
    candidates.append(code.replace(' ', '').upper())

    for c in candidates:
        if c in aquant_price_map:
            found_price = aquant_price_map[c]
            break

    if found_price:
        stored[i]['price'] = found_price
        fix_count += 1
        print(f"  ✅ [{i:04d}] {code} → ₹{found_price}")
    else:
        still_zero.append((i, item))

print(f"\nAquant prices fixed: {fix_count}")

# ============================================================
# STEP C: Delete garbage Kohler entries
# ============================================================
print("\n--- Removing garbage Kohler entries ---")

GARBAGE_PATTERNS = [
    r'IMAGE[\s_]?NOT[\s_]?FOUND',   # IMAGE NOT FOUND, IMAGE_NOT_FOUND
    r'\.PDF$',                        # codes ending in .PDF
    r'\([^)]+\)$',                    # codes like K-38886IN-4ND-BRD(K-38886IN-4ND-BRD)
    r'^K-10\d{5}$',                  # K-1060831 etc (spare parts, no price in book)
    r'^K-12\d{5}',                   # K-1213309
    r'^K-15\d{5}',                   # K-1527926
    r'^K-16\d{5}',                   # K-1628469
]

# Specific codes to remove (confirmed garbage)
SPECIFIC_REMOVE = {
    'IMAGE NOT FOUND',
    'IMAGE_NOT_FOUND',
}

garbage_indices = []
for i, item in enumerate(stored):
    if item.get('brand') != 'Kohler':
        continue
    price = str(item.get('price', '0')).strip()
    if price not in ['0', '', 'None', 'null', '0.0']:
        continue

    code = (item.get('search_code') or item.get('base_code') or '').strip()
    name = item.get('name', '')

    is_garbage = False

    if code in SPECIFIC_REMOVE or name in SPECIFIC_REMOVE:
        is_garbage = True

    for pattern in GARBAGE_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE) or re.search(pattern, name, re.IGNORECASE):
            is_garbage = True
            break

    if is_garbage:
        garbage_indices.append(i)
        print(f"  🗑️  [{i:04d}] REMOVING: {code} | {name[:50]}")

# Remove in reverse order to preserve indices
for i in sorted(garbage_indices, reverse=True):
    stored.pop(i)

print(f"\nGarbage entries removed: {len(garbage_indices)}")
print(f"Index size now: {len(stored)}")

# ============================================================
# STEP D: Final summary
# ============================================================
remaining_zero = [(i, it) for i, it in enumerate(stored)
                  if str(it.get('price','0')).strip() in ['0','','None','null','0.0']]

print(f"\n{'='*60}")
print(f"REMAINING price=0 after all fixes: {len(remaining_zero)}")
for i, item in remaining_zero:
    code = item.get('search_code') or item.get('base_code') or 'N/A'
    brand = item.get('brand','?')
    src = item.get('source','?')
    print(f"  [{i:04d}] [{brand}] {code} | src:{src}")

# ============================================================
# SAVE
# ============================================================
print(f"\nSaving index ({len(stored)} items)...")
data['stored_items'] = stored
with open(INDEX_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print("✅ search_index_v2.json saved!")
