import sys
import os
import json
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import pdf_reader

pdf_path = r'c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\uploads\Aquant Price List Vol. 14 Feb. 2025 - Low Res Searchable.pdf'

original_doc_open = pdf_reader.fitz.open
def mock_open(*args, **kwargs):
    doc = original_doc_open(*args, **kwargs)
    class MockDoc:
        def __init__(self, doc):
            self.doc = doc
        def __len__(self):
            return 1
        def __getitem__(self, idx):
            return self.doc[3] # ONLY page 4
    return MockDoc(doc)

pdf_reader.fitz.open = mock_open

items = pdf_reader.extract_content(pdf_path)
for item in items[:15]:
    print(f"Name: {item.get('name')} | Price: {item.get('price')} | Img: {item.get('images')}")
