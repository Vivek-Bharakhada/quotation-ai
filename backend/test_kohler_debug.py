import fitz
import re

doc = fitz.open("uploads/Kohler_PriceBook_Nov'25 Edition (1).pdf")

KOHLER_CATS = [
    "TOILETS", "SMART TOILETS & BIDET SEATS", "1 PC TOILETS & WALL HUNGS",
    "IN-WALL TANKS", "FACEPLATES", "MIRRORS", "VANITIES", "WASH BASINS",
    "FAUCETS", "SHOWERING", "STEAM", "SHOWER ENCLOSURES", "FITTINGS",
    "ACCESSORIES", "VIBRANT FINISHES", "FRENCH GOLD", "BRUSHED BRONZE",
    "ROSE GOLD", "MATTE BLACK", "BRUSHED ROSE GOLD", "KITCHEN SINKS & FAUCETS",
    "BATHTUBS & BATH FILLERS", "COMMERCIAL PRODUCTS", "CLEANING SOLUTIONS"
]

cat = None
cats = {}
for page_num in range(doc.page_count):
    page = doc[page_num]
    blocks = page.get_text("blocks")
    blocks.sort(key=lambda b: (b[1], b[0]))
    
    for b in blocks:
        if b[6] != 0: continue
        text = b[4].strip()
        t_up = text.upper().replace('\n', ' ')
        x0, y0, x1, y1 = b[:4]
        
        best_match = None
        best_len = 0
        for kc in KOHLER_CATS:
            if kc in t_up and len(text) < 50:
                if len(kc) > best_len:
                    best_len = len(kc)
                    best_match = kc
        if best_match and y0 < 100:
            cat = best_match
            continue
            
        if x0 > 100 and "K-" in text and "MRP" in text:
            cats[cat] = cats.get(cat, 0) + 1

from collections import Counter
print(Counter(cats).most_common(20))
