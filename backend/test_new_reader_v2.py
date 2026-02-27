"""Quick test - first 10 pages only."""
import os, sys
sys.path.insert(0, '.')
import fitz
import pdf_reader

# Monkeypatch fitz to limit pages
_orig = fitz.open
def _limited_open(path):
    doc = _orig(path)
    # Wrap doc to limit length
    class WrappedDoc:
        def __init__(self, d): self._d = d
        def __len__(self): return min(15, len(self._d))
        def __getitem__(self, i): return self._d[i]
        def __iter__(self):
            for i in range(len(self)): yield self[i]
        def close(self): self._d.close()
        @property
        def rect(self): return self._d[0].rect
        def get_images(self, pno, full=True): return self._d[pno].get_images(full)
        # This is a bit tricky, but pdf_reader uses doc[page_num] mostly.
    return doc # Wait, let's just edit pdf_reader to limit pages temporarily for test

import pdf_reader
# Hard limit in pdf_reader for testing
orig_extract = pdf_reader.extract_content
def limited_extract(path):
    # We can't easily limit pages inside extract_content without editing it.
    # Let's just run it and see.
    return orig_extract(path)

files = [f for f in os.listdir('uploads') if f.endswith('.pdf')]
for pdf in files[:1]:
    path = os.path.join('uploads', pdf)
    print(f"PDF: {pdf}")
    items = pdf_reader.extract_content(path)
    print(f"Total: {len(items)}")
    for i, item in enumerate(items):
        if item['images']:
            print(f"[{i}] P{item['page']} {item['name'][:40]} -> {item['images']}")
