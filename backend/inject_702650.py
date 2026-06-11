import json
import os
import re

def main():
    index_path = 'backend/search_index_v2.json'
    
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    stored_items = data.get('stored_items', [])
    
    # 702650IN variants
    products = [
        {
            "brand": "Kohler",
            "source": "Kohler_PriceBook (June'26).pdf",
            "page": 74,
            "search_code": "K-702650IN-RH0-AF",
            "base_code": "K-702650IN",
            "price": "135000.00",
            "name": "Framed sliding enclosure - Right door",
            "text": "Framed sliding enclosure - Right door Width: 1300mm-1700mm Height: 2200mm",
            "images": ["/static/images/Kohler/K-702650IN-RH0-AF.png"]
        },
        {
            "brand": "Kohler",
            "source": "Kohler_PriceBook (June'26).pdf",
            "page": 74,
            "search_code": "K-702650IN-LH0-AF",
            "base_code": "K-702650IN",
            "price": "135000.00",
            "name": "Framed sliding enclosure - Left door",
            "text": "Framed sliding enclosure - Left door Width: 1300mm-1700mm Height: 2200mm",
            "images": ["/static/images/Kohler/K-702650IN-LH0-AF.png"]
        },
        {
            "brand": "Kohler",
            "source": "Kohler_PriceBook (June'26).pdf",
            "page": 74,
            "search_code": "K-702650IN-RH0-BL",
            "base_code": "K-702650IN",
            "price": "145000.00",
            "name": "Framed sliding enclosure - Right door",
            "text": "Framed sliding enclosure - Right door Width: 1300mm-1700mm Height: 2200mm",
            "images": ["/static/images/Kohler/K-702650IN-RH0-BL.png"]
        },
        {
            "brand": "Kohler",
            "source": "Kohler_PriceBook (June'26).pdf",
            "page": 74,
            "search_code": "K-702650IN-LH0-BL",
            "base_code": "K-702650IN",
            "price": "145000.00",
            "name": "Framed sliding enclosure - Left door",
            "text": "Framed sliding enclosure - Left door Width: 1300mm-1700mm Height: 2200mm",
            "images": ["/static/images/Kohler/K-702650IN-LH0-BL.png"]
        }
    ]
    
    codes_to_remove = set([p["search_code"] for p in products])
    filtered_items = [i for i in stored_items if i.get("search_code") not in codes_to_remove]
    filtered_items.extend(products)
    
    data['stored_items'] = filtered_items
    
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
        
    import sys
    sys.path.append(os.path.abspath('backend'))
    import search_engine
    search_engine.load_index()
    search_engine.index_local_catalogs()
    import mongodb
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    mongodb.save_search_index(data)
    print("MongoDB Push Complete.")

if __name__ == "__main__":
    main()
