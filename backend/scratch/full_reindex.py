import os
import re
import search_engine
import pdf_reader
import importlib

# Reload modules to ensure latest logic is used
importlib.reload(pdf_reader)
importlib.reload(search_engine)

print("Starting full re-index with improved code detection...")

# Reset index
search_engine.reset_index()

uploads_dir = r"c:\Movies\quotation-ai\quotation-ai\backend\uploads"
total_indexed = 0

files = [f for f in os.listdir(uploads_dir) if f.lower().endswith(".pdf")]
for filename in files:
    brand = ""
    if "aquant" in filename.lower():
        brand = "Aquant"
    elif "kohler" in filename.lower():
        brand = "Kohler"
    elif "plumber" in filename.lower():
        brand = "Plumber"
    else:
        continue

    path = os.path.join(uploads_dir, filename)
    print(f"Indexing {filename} as {brand}...")
    try:
        items = pdf_reader.extract_content(path)
        # Set brand on all items before indexing
        for item in items:
            if "brand" not in item or not item["brand"]:
                item["brand"] = brand
        
        search_engine.add_to_index(None, items)
        total_indexed += len(items)
        print(f"DONE: {len(items)} items from {filename}")
    except Exception as e:
        print(f"ERROR indexing {filename}: {e}")
        import traceback
        traceback.print_exc()

print("Saving final index...")
search_engine.save_index()
print(f"Finished! Total items indexed: {total_indexed}")
