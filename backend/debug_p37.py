import pdf_reader
import json

res = pdf_reader.extract_content('uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf', max_pages=38)
p37 = [it for it in res if it.get('page') == 37]

print(f"Items found on Page 37: {len(p37)}")
for it in p37:
    name = it.get('name', 'N/A')
    cx = it.get('cx', 'N/A')
    cy = it.get('cy', 'N/A')
    imgs = it.get('images', [])
    print(f"  Item: {name[:50]:50} | CX: {cx:6}, CY: {cy:6} | Imgs: {len(imgs)}")
