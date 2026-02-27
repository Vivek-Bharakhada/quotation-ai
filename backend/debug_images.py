import os, sys
sys.path.insert(0, '.')
import fitz
import pdf_reader

# Find the path
files = [f for f in os.listdir('uploads') if 'Aquant' in f and f.endswith('.pdf')]
if not files:
    print("No Aquant PDF found")
    sys.exit(1)

path = os.path.join('uploads', files[0])
doc = fitz.open(path)
print(f"Testing first 10 pages of {path}...")
for page_num in range(10):
    print(f"\nProcessing Page {page_num+1}")
    items = pdf_reader.extract_content(path, max_pages=page_num+1)
    # This will return ALL items from 0 to page_num+1. 
    # Let's filter only for the current page
    for item in items:
        if item['page'] == page_num + 1:
            if item['images']:
                print(f"  [FOUND IMG] {item['name'][:40]} -> {item['images']}")
            else:
                print(f"  [NO IMG]    {item['name'][:40]}")
doc.close()
