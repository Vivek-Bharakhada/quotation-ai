import json
import os
import sys
sys.path.append(os.path.abspath('backend'))
import search_engine
import fitz
import re

def main():
    print("Starting full clean index generation...")
    index_path = 'backend/search_index_v2.json'
    aquant_pdf = 'backend/uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf'
    
    # Reload from current state
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    items = data.get('stored_items', [])
    
    kohler_items = [i for i in items if i.get('brand') == 'Kohler']
    aquant_items = [i for i in items if i.get('brand') == 'Aquant']
    
    print(f"Initial counts -> Kohler: {len(kohler_items)}, Aquant: {len(aquant_items)}")
    
    # -------------------
    # 1. Kohler Dedupe
    # -------------------
    unique_kohler = {}
    for item in kohler_items:
        code = item.get('search_code')
        if not code: continue
            
        if code not in unique_kohler:
            unique_kohler[code] = item
        else:
            existing = unique_kohler[code]
            e_source = existing.get('source', '')
            i_source = item.get('source', '')
            
            e_is_june = 'June' in e_source
            i_is_june = 'June' in i_source
            
            if i_is_june and not e_is_june:
                unique_kohler[code] = item
            elif e_is_june and not i_is_june:
                pass
            else:
                if len(item.get('images', [])) > len(existing.get('images', [])):
                    unique_kohler[code] = item
                elif len(item.get('text', '')) > len(existing.get('text', '')):
                    unique_kohler[code] = item
                    
    # Inject missing enclosures
    enclosures = [
        {"brand": "Kohler", "source": "Kohler_PriceBook (June'26).pdf", "page": 74, "search_code": "K-702650IN-RH0-AF", "base_code": "K-702650IN", "price": "135000.00", "name": "Framed sliding enclosure - Right door", "text": "Framed sliding enclosure - Right door Width: 1300mm-1700mm Height: 2200mm", "images": ["/static/images/Kohler/K-702650IN-RH0-AF.png"]},
        {"brand": "Kohler", "source": "Kohler_PriceBook (June'26).pdf", "page": 74, "search_code": "K-702650IN-LH0-AF", "base_code": "K-702650IN", "price": "135000.00", "name": "Framed sliding enclosure - Left door", "text": "Framed sliding enclosure - Left door Width: 1300mm-1700mm Height: 2200mm", "images": ["/static/images/Kohler/K-702650IN-LH0-AF.png"]},
        {"brand": "Kohler", "source": "Kohler_PriceBook (June'26).pdf", "page": 74, "search_code": "K-702650IN-RH0-BL", "base_code": "K-702650IN", "price": "145000.00", "name": "Framed sliding enclosure - Right door", "text": "Framed sliding enclosure - Right door Width: 1300mm-1700mm Height: 2200mm", "images": ["/static/images/Kohler/K-702650IN-RH0-BL.png"]},
        {"brand": "Kohler", "source": "Kohler_PriceBook (June'26).pdf", "page": 74, "search_code": "K-702650IN-LH0-BL", "base_code": "K-702650IN", "price": "145000.00", "name": "Framed sliding enclosure - Left door", "text": "Framed sliding enclosure - Left door Width: 1300mm-1700mm Height: 2200mm", "images": ["/static/images/Kohler/K-702650IN-LH0-BL.png"]}
    ]
    for enc in enclosures:
        unique_kohler[enc["search_code"]] = enc

    # -------------------
    # 2. Aquant Prices & Dedupe
    # -------------------
    doc = fitz.open(aquant_pdf)
    page_texts = {}
    for i in range(len(doc)):
        text = doc[i].get_text("text").splitlines()
        page_texts[i] = [line.strip() for line in text if line.strip()]
        
    def find_price_backwards(page_num, search_code):
        if page_num < 0 or page_num >= len(doc): return "0"
        lines = page_texts[page_num]
        code_idx = -1
        base = search_code.split(' ')[0] if ' ' in search_code else search_code
        for idx, line in enumerate(lines):
            if base in line or search_code in line:
                code_idx = idx
                break
        if code_idx != -1:
            for check_idx in range(code_idx - 1, max(-1, code_idx - 10), -1):
                line = lines[check_idx]
                m = re.search(r'([\d,]+)(?:\.\d{2})?', line)
                if m and ('MRP' in line or '`' in line or 'Rs' in line):
                    return m.group(1).replace(',', '')
            for check_idx in range(code_idx + 1, min(len(lines), code_idx + 10)):
                line = lines[check_idx]
                m = re.search(r'([\d,]+)(?:\.\d{2})?', line)
                if m and ('MRP' in line or '`' in line or 'Rs' in line):
                    return m.group(1).replace(',', '')
        return "0"

    aquant_fixed = 0
    unique_aquant = {}
    
    for item in aquant_items:
        code = item.get('search_code')
        if not code: continue
        
        # Try fix price
        price = str(item.get('price', '')).strip()
        if price in ('0', '0.0', '0.00', '', 'None'):
            page = item.get('page', 0)
            found_price = find_price_backwards(page, code)
            if found_price == "0" and page > 0:
                found_price = find_price_backwards(page - 1, code)
            if found_price != "0":
                item['price'] = found_price
                aquant_fixed += 1
                
        # Dedupe Aquant
        if code not in unique_aquant:
            unique_aquant[code] = item
        else:
            existing = unique_aquant[code]
            e_price = float(str(existing.get('price', '0')).replace(',', ''))
            i_price = float(str(item.get('price', '0')).replace(',', ''))
            if i_price > 0 and e_price == 0:
                unique_aquant[code] = item
            elif e_price > 0 and i_price == 0:
                pass
            else:
                if len(item.get('images', [])) > len(existing.get('images', [])):
                    unique_aquant[code] = item

    final_kohler = list(unique_kohler.values())
    final_aquant = list(unique_aquant.values())
    
    print(f"Final counts -> Kohler: {len(final_kohler)}, Aquant: {len(final_aquant)}")
    print(f"Fixed {aquant_fixed} Aquant zero prices.")
    
    data['stored_items'] = final_kohler + final_aquant
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print("Rebuilding FAISS index & assigning images...")
    search_engine._sanitize_item_images(data['stored_items'])
    search_engine._normalize_item_images(data['stored_items'])
    
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    import mongodb
    from dotenv import load_dotenv
    load_dotenv('backend/.env')
    
    mongodb.save_search_index(data)
    
    search_engine.load_index(force=True)
    print("Done.")

if __name__ == "__main__":
    main()
