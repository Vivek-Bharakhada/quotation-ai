import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Movies\quotation-ai\quotation-ai\backend\search_index_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

stored = data['stored_items']

# ---- ISSUE 1: Price = 0 ----
price_zero = [(i, item) for i, item in enumerate(stored)
              if str(item.get('price', '0')).strip() in ['0', '', 'None', 'null', '0.0']]

# ---- ISSUE 2: No image ----
no_image = [(i, item) for i, item in enumerate(stored)
            if not item.get('images') or item.get('images') == []]

# ---- ISSUE 3: Image file missing on disk ----
static_root = r'C:\Movies\quotation-ai\quotation-ai\backend'
missing_image_file = []
for i, item in enumerate(stored):
    imgs = item.get('images', [])
    if imgs:
        img_path = imgs[0].lstrip('/')
        full_path = os.path.join(static_root, img_path)
        if not os.path.exists(full_path):
            missing_image_file.append((i, item, imgs[0]))

# ---- WRITE REPORT ----
output_lines = []

output_lines.append(f"{'='*60}")
output_lines.append(f"FULL AUDIT REPORT — {len(stored)} total items")
output_lines.append(f"{'='*60}\n")

output_lines.append(f"[1] PRICE = 0  →  {len(price_zero)} items")
output_lines.append(f"[2] NO IMAGE entry  →  {len(no_image)} items")
output_lines.append(f"[3] Image file MISSING on disk  →  {len(missing_image_file)} items")

# --- Price Zero breakdown by brand ---
output_lines.append(f"\n{'='*60}")
output_lines.append(f"PRICE = 0 BREAKDOWN")
output_lines.append(f"{'='*60}")
kohler_zero = [(i, it) for i, it in price_zero if it.get('brand') == 'Kohler']
aquant_zero = [(i, it) for i, it in price_zero if it.get('brand') == 'Aquant']
output_lines.append(f"Kohler: {len(kohler_zero)}  |  Aquant: {len(aquant_zero)}")
output_lines.append("")
for i, item in price_zero:
    code = item.get('search_code') or item.get('base_code') or 'N/A'
    name = item.get('name', 'N/A')[:60]
    brand = item.get('brand', 'N/A')
    source = item.get('source', 'N/A')
    output_lines.append(f"  [{i:04d}] [{brand}] {code} | {name} | src:{source}")

# --- Missing image on disk ---
output_lines.append(f"\n{'='*60}")
output_lines.append(f"IMAGE FILE MISSING ON DISK")
output_lines.append(f"{'='*60}")
for i, item, img in missing_image_file:
    code = item.get('search_code') or item.get('base_code') or 'N/A'
    brand = item.get('brand', 'N/A')
    output_lines.append(f"  [{i:04d}] [{brand}] {code} | img: {img}")

# --- No image entries ---
output_lines.append(f"\n{'='*60}")
output_lines.append(f"NO IMAGE ENTRY")
output_lines.append(f"{'='*60}")
for i, item in no_image:
    code = item.get('search_code') or item.get('base_code') or 'N/A'
    brand = item.get('brand', 'N/A')
    name = item.get('name', 'N/A')[:60]
    output_lines.append(f"  [{i:04d}] [{brand}] {code} | {name}")

report = '\n'.join(output_lines)

out_path = r'C:\Movies\quotation-ai\quotation-ai\backend\scratch\audit_report.txt'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(report)

print(report)
print(f"\nReport saved to: {out_path}")
