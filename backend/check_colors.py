import json
from collections import defaultdict
import re

items = json.load(open("search_index_v2.json"))["stored_items"]
aquant = [i for i in items if i.get("brand") == "Aquant"]

base_to_variants = defaultdict(list)
for i in aquant:
    code = i.get("search_code", "")
    price = i.get("price", "0")
    name = i.get("name", "")
    
    # Try to extract base code
    parts = code.split()
    if "+" in code:
        pass # Skip combo for this analysis
    elif len(parts) > 1 and parts[-1] in ["CP", "BRG", "BG", "GG", "MB", "RG", "BSS", "CM", "PP", "BM", "RB", "LM", "MI", "MG", "TCR", "OG", "W", "B", "AB"]:
        base = " ".join(parts[:-1])
        variant = parts[-1]
        base_to_variants[base].append((variant, price, name))
    else:
        # Just use the code as base if no known finish
        base_to_variants[code].append(("BASE", price, name))

# Let's count how many items have multiple variants
multi_variant_bases = {b: v for b, v in base_to_variants.items() if len(v) > 1}

print(f"Total base products with multiple variants: {len(multi_variant_bases)}")

# Let's show a few examples to see if they look correct
count = 0
for b, variants in list(multi_variant_bases.items())[:20]:
    print(f"\nBase: {b}")
    for v, p, n in variants:
        print(f"  - {v:5s} | MRP: {p:7s} | {n[:50]}")
    count += 1

# Check if there are color variants that SHARE the SAME code (which would be a bug)
# (i.e. if the PDF has "Color: Black", "Color: White" but the code is just "1234" for both)
same_code_diff_price = defaultdict(list)
for i in aquant:
    same_code_diff_price[i.get("search_code", "")].append(i)

print("\n--- Items with same code but multiple entries ---")
for code, itms in same_code_diff_price.items():
    if len(itms) > 1:
        prices = [it.get("price", "0") for it in itms]
        names = [it.get("name", "") for it in itms]
        if len(set(prices)) > 1 or len(set(names)) > 1:
            print(f"Code: {code}")
            for it in itms:
                print(f"  P{it.get('page')} | MRP: {it.get('price','0'):7s} | {it.get('name','')[:50]}")

