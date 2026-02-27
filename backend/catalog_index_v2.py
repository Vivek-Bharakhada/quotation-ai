@app.get("/catalog/index")
def get_catalog_index():
    import search_engine
    import re
    
    # Force load if empty
    if not search_engine.stored_items:
        search_engine.load_index()
        
    print(f"DEBUG: Generating index for {len(search_engine.stored_items)} items")
    
    brand_map = {}
    for item in search_engine.stored_items:
        src = str(item.get("source") or "Generic").lower()
        # Clean brand identification
        brand = "Kohler" if "kohler" in src else "Aquant" if "aquant" in src else "Other"
        
        if brand not in brand_map:
            brand_map[brand] = {"name": brand, "collections": set()}
        
        # Try to find a "Heading" like "WASHBASIN" or "SHOWER" in the text
        text = item["text"].strip()
        if not text: continue
        
        first_line = text.split("\n")[0].strip()
        # Look for words in all caps that are 4+ characters
        heading_match = re.search(r'^([A-Z\s]{4,})', first_line)
        if heading_match:
            h = heading_match.group(1).strip()
            h = re.sub(r'\s+', ' ', h)
            if 3 < len(h) < 25: 
                brand_map[brand]["collections"].add(h)

    # Convert to list
    result = []
    # Always include the big two if there's any data
    target_brands = ["Aquant", "Kohler"]
    for b_name in target_brands:
        b_data = brand_map.get(b_name, {"name": b_name, "collections": set()})
        cols = sorted(list(b_data["collections"]))
        if not cols: cols = ["General Inventory"]
        
        result.append({
            "brand": b_name,
            "collections": cols[:15], # More for better selection
            "count": len(search_engine.stored_items) # Placeholder for total
        })
    
    # Add any other brands discovered
    for b_name, b_data in brand_map.items():
        if b_name not in target_brands and b_name != "Other":
            cols = sorted(list(b_data["collections"])) or ["General Inventory"]
            result.append({
                "brand": b_name,
                "collections": cols[:15]
            })

    print(f"DEBUG: Returning {len(result)} brands")
    return result
