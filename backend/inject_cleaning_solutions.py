import json
import os
import re

def main():
    index_path = 'backend/search_index_v2.json'
    
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    stored_items = data.get('stored_items', [])
    
    # Define the 7 products manually
    products = [
        {
            "brand": "Kohler",
            "source": "Kohler_PriceBook (June'26).pdf",
            "page": 168,
            "search_code": "1339378",
            "base_code": "1339378",
            "price": "799.00",
            "name": "Surface Cleaner (500ml)",
            "text": "Surface Cleaner Qty: 500ml Format: Ready to use Usage Area: Faucets, showerheads, health faucets and other fittings in CP",
            "images": ["/static/images/Kohler/1339378.png"]
        },
        {
            "brand": "Kohler",
            "source": "Kohler_PriceBook (June'26).pdf",
            "page": 168,
            "search_code": "1352426",
            "base_code": "1352426",
            "price": "498.00",
            "name": "Glass Surface Cleaner (1 L)",
            "text": "Glass Surface Cleaner Qty: 1 L Format: Concentrate Usage Area: Glass surfaces, mirrors",
            "images": ["/static/images/Kohler/1352426.png"]
        },
        {
            "brand": "Kohler",
            "source": "Kohler_PriceBook (June'26).pdf",
            "page": 168,
            "search_code": "1352425",
            "base_code": "1352425",
            "price": "450.00",
            "name": "Surface Cleaner For Toilet Seats & Tiles (1L)",
            "text": "Surface Cleaner (For Toilet Seats & Tiles) Qty: 1L Format: Concentrate Usage Area: Toilets seats, multiple hard surfaces",
            "images": ["/static/images/Kohler/1352425.png"]
        },
        {
            "brand": "Kohler",
            "source": "Kohler_PriceBook (June'26).pdf",
            "page": 168,
            "search_code": "1352427",
            "base_code": "1352427",
            "price": "160.00",
            "name": "Toilet Bowl Cleaner (500ml)",
            "text": "Toilet Bowl Cleaner Qty: 500ml Format: Ready to use Usage Area: Inside toilet bowls",
            "images": ["/static/images/Kohler/1352427.png"]
        },
        {
            "brand": "Kohler",
            "source": "Kohler_PriceBook (June'26).pdf",
            "page": 168,
            "search_code": "1563946",
            "base_code": "1563946",
            "price": "999.00",
            "name": "Faucet Cleaner (500ml)",
            "text": "Faucet Cleaner Qty: 500ml Format: Ready to use Usage Area: Coloured finishes on faucets, showerheads, health faucets & other fittings",
            "images": ["/static/images/Kohler/1563946.png"]
        },
        {
            "brand": "Kohler",
            "source": "Kohler_PriceBook (June'26).pdf",
            "page": 168,
            "search_code": "39208IN-NA",
            "base_code": "39208IN-NA",
            "price": "1200.00",
            "name": "Stainless Steel Kitchen Sink Cleaner (190ml)",
            "text": "Stainless Steel Kitchen Sink Cleaner Qty: 190ml Format: Ready to use Usage Area: Kitchen sinks",
            "images": ["/static/images/Kohler/39208IN-NA.png"]
        },
        {
            "brand": "Kohler",
            "source": "Kohler_PriceBook (June'26).pdf",
            "page": 168,
            "search_code": "32989IN-NA",
            "base_code": "32989IN-NA",
            "price": "2000.00",
            "name": "Neoroc Kitchen Sink Cleaner",
            "text": "Neoroc Kitchen Sink Cleaner Qty: 2*50ml Descaler + 1*50ml Easy Clean + 1*Scrubbing Pad Format: Ready to use Usage Area: Kitchen sinks",
            "images": ["/static/images/Kohler/32989IN-NA.png"]
        }
    ]
    
    # Remove existing to prevent duplicates
    codes_to_remove = set([p["search_code"] for p in products])
    filtered_items = [i for i in stored_items if i.get("search_code") not in codes_to_remove]
    
    # Append the products
    filtered_items.extend(products)
    
    data['stored_items'] = filtered_items
    
    # Rebuild keyword index
    keyword_index = {}
    import sys
    sys.path.append(os.path.abspath('backend'))
    from search_engine import _clean_display_text
    
    for i, item in enumerate(data['stored_items']):
        text = _clean_display_text(item.get("name", "") + " " + item.get("text", ""))
        words = re.findall(r'\b\w+\b', text.lower())
        if "search_code" in item:
            parts = str(item["search_code"]).split(' + ')
            for p in parts:
                words.append(p.lower())
        for w in set(words):
            if len(w) > 1:
                keyword_index.setdefault(w, []).append(i)
                
    data['keyword_index'] = keyword_index
    
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    print(f"Injected {len(products)} products from Page 168.")
    
    import mongodb
    mongodb.save_search_index(data)
    print("MongoDB Push Complete.")

if __name__ == "__main__":
    main()
