import sys
import os
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
            return 2
        def __getitem__(self, idx):
            # Pages 73, 74 are index 72, 73
            return self.doc[72 + idx]
    return MockDoc(doc)

pdf_reader.fitz.open = mock_open
pdf_reader.image_dir = 'backend/uploads/extracted_images'
try:
    os.makedirs(pdf_reader.image_dir, exist_ok=True)
except Exception:
    pass

items = pdf_reader.extract_content(pdf_path)
for item in items:
    print(f"[{item.get('category')}] {item.get('name')} | {item.get('price')}")
