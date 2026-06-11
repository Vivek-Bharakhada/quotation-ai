import json
import os

def main():
    index_path = 'backend/search_index_v2.json'
    
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    stored_items = data.get('stored_items', [])
    
    kohler_items = [i for i in stored_items if i.get('brand') == 'Kohler']
    other_items = [i for i in stored_items if i.get('brand') != 'Kohler']
    
    unique_kohler = {}
    
    for item in kohler_items:
        code = item.get('search_code')
        if not code:
            continue
            
        if code not in unique_kohler:
            unique_kohler[code] = item
        else:
            existing = unique_kohler[code]
            
            # Prefer June '26 over March '26
            e_source = existing.get('source', '')
            i_source = item.get('source', '')
            
            e_is_june = 'June' in e_source
            i_is_june = 'June' in i_source
            
            if i_is_june and not e_is_june:
                unique_kohler[code] = item
            elif e_is_june and not i_is_june:
                pass
            else:
                # Both are June or both are March
                # Prefer the one with more images? Or shorter text?
                if len(item.get('images', [])) > len(existing.get('images', [])):
                    unique_kohler[code] = item
                elif len(item.get('text', '')) > len(existing.get('text', '')):
                    unique_kohler[code] = item
                    
    final_items = other_items + list(unique_kohler.values())
    
    data['stored_items'] = final_items
    
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
    print(f"Deduplication complete. Reduced Kohler items to {len(unique_kohler)}. Total items: {len(final_items)}.")
    
if __name__ == "__main__":
    main()
