import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import pdf_reader

pdf_path = r'backend/uploads/Aquant Price List Vol. 14 Feb. 2025 - Low Res Searchable.pdf'

original_doc_open = pdf_reader.fitz.open
def mock_open(*args, **kwargs):
    doc = original_doc_open(*args, **kwargs)
    class MockDoc:
        def __init__(self, doc):
            self.doc = doc
        def __len__(self):
            return 1
        def __getitem__(self, idx):
            return self.doc[25] # Page 26
    return MockDoc(doc)

pdf_reader.fitz.open = mock_open

items = pdf_reader.extract_content(pdf_path)
print("EXTRACTED:")
for item in items:
    print(item.get('name'), "|||", item.get('category'))
