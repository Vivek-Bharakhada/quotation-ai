import sys; sys.path.append('backend'); import pdf_reader
import fitz
doc = fitz.open(r'backend/uploads/Aquant Price List Vol. 14 Feb. 2025 - Low Res Searchable.pdf')

class MockDoc:
    def __init__(self, doc): self.doc = doc
    def __len__(self): return 1
    def __getitem__(self, idx): return self.doc[19]

pdf_reader.fitz.open = lambda *a, **k: MockDoc(doc)
res = pdf_reader.extract_content('test')
for r in res:
    print(r.get('name'), "||", r.get('category'))
