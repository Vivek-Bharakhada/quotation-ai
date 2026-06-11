import fitz
import json
import re

def fix_aquant_prices_and_dedupe():
    index_path = 'backend/search_index_v2.json'
    pdf_path = 'backend/uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf'
    
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    aquant = [i for i in data.get('stored_items', []) if i.get('brand') == 'Aquant']
    kohler = [i for i in data.get('stored_items', []) if i.get('brand') == 'Kohler']
    
    doc = fitz.open(pdf_path)
    
    # Pre-parse all text from PDF to find prices
    # Aquant prices are usually plain numbers like 1,450 or 2,500 without MRP prefix sometimes
    page_texts = {}
    for i in range(len(doc)):
        text = doc[i].get_text("text").splitlines()
        page_texts[i] = [line.strip() for line in text if line.strip()]
        
    def find_price_backwards(page_num, search_code):
        if page_num < 0 or page_num >= len(doc):
            return "0"
            
        lines = page_texts[page_num]
        
        # Find the index of the code
        code_idx = -1
        # Also clean the search_code
        base = search_code.split(' ')[0] if ' ' in search_code else search_code
        
        for idx, line in enumerate(lines):
            if base in line or search_code in line:
                code_idx = idx
                break
                
        if code_idx != -1:
            # Look backwards up to 10 lines for a price
            for check_idx in range(code_idx - 1, max(-1, code_idx - 10), -1):
                line = lines[check_idx]
                # Price is usually just digits and commas, maybe ends with ' MRP' or just digits
                m = re.search(r'([\d,]+)(?:\.\d{2})?', line)
                if m and ('MRP' in line or '`' in line or 'Rs' in line):
                    return m.group(1).replace(',', '')
                    
            # Look forwards up to 10 lines
            for check_idx in range(code_idx + 1, min(len(lines), code_idx + 10)):
                line = lines[check_idx]
                m = re.search(r'([\d,]+)(?:\.\d{2})?', line)
                if m and ('MRP' in line or '`' in line or 'Rs' in line):
                    return m.group(1).replace(',', '')
                    
        return "0"

    fixed_count = 0
    # First, fix prices
    for item in aquant:
        price = str(item.get('price', '')).strip()
        if price in ('0', '0.0', '0.00', '', 'None'):
            code = item.get('search_code', '')
            page = item.get('page', 0)
            
            # Since page might be 1-indexed in UI but 0-indexed in fitz
            found_price = find_price_backwards(page, code)
            if found_price == "0" and page > 0:
                found_price = find_price_backwards(page - 1, code)
                
            if found_price != "0":
                item['price'] = found_price
                fixed_count += 1
                
    # Deduplicate
    unique_aquant = {}
    for item in aquant:
        code = item.get('search_code')
        if not code:
            continue
            
        if code not in unique_aquant:
            unique_aquant[code] = item
        else:
            existing = unique_aquant[code]
            e_price = float(str(existing.get('price', '0')).replace(',', ''))
            i_price = float(str(item.get('price', '0')).replace(',', ''))
            
            # Prefer the one with a valid price > 0
            if i_price > 0 and e_price == 0:
                unique_aquant[code] = item
            elif e_price > 0 and i_price == 0:
                pass
            else:
                # Both have price or both don't
                if len(item.get('images', [])) > len(existing.get('images', [])):
                    unique_aquant[code] = item
                    
    final_aquant = list(unique_aquant.values())
    
    data['stored_items'] = kohler + final_aquant
    
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    print(f"Fixed {fixed_count} zero prices. Reduced to {len(final_aquant)} unique Aquant items.")
    
    import sys
    import os
    sys.path.append(os.path.abspath('backend'))
    import mongodb
    mongodb.save_search_index(data)
    print("Saved to MongoDB.")

if __name__ == "__main__":
    fix_aquant_prices_and_dedupe()
