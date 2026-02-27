import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import pdf_reader

pdf_path = r'c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\uploads\Aquant Price List Vol. 14 Feb. 2025 - Low Res Searchable.pdf'

# Monkey patch extract_content to only run page 4 (index 3)
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
for item in items:
    print(f"\n--- Item ---")
    print(f"Name: {item.get('name')}")
    print(f"Price: {item.get('price')}")
    print(f"Cat: {item.get('category')}")
    print(f"Images: {item.get('images')}")
    print(f"Text:\n{item.get('text')}")
