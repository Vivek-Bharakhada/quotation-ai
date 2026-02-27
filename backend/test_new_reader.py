"""Quick test - only 5 pages of first PDF."""
import os, sys
sys.path.insert(0, '.')
import fitz
from pdf_reader import extract_content

# Monkeypatch to only read first 5 pages
_orig = fitz.open
def _limited_open(path):
    doc = _orig(path)
    class LimitedDoc:
        def __init__(self, d): self._d = d
        def __len__(self): return min(8, len(self._d))
        def __getitem__(self, i): return self._d[i]
        def get_toc(self): return []
        def __iter__(self):
            for i in range(len(self)): yield self[i]
        def close(self): self._d.close()
    return LimitedDoc(doc)

fitz.open = _limited_open

files = [f for f in os.listdir('uploads') if f.endswith('.pdf')]
for pdf in files[:1]:  # Only Aquant
    path = os.path.join('uploads', pdf)
    print(f"PDF: {pdf[:50]}")
    items = extract_content(path)
    print(f"Total extracted items: {len(items)}")
    for i, item in enumerate(items[:15]):
        print(f"\n[{i+1}] page={item['page']} price={item.get('price','?')}")
        print(f"  Name: {item.get('name','')[:80]}")
        print(f"  Text: {item['text'][:120]}")
        print(f"  Img:  {item['images']}")
