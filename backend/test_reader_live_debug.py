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
            return 1
        def __getitem__(self, idx):
            return self.doc[3] # ONLY page 4
    return MockDoc(doc)

pdf_reader.fitz.open = mock_open

# We will inject some print statements into pdf_reader dynamically if we can,
# or just redefine the image loop locally to see what numbers it gets

items = pdf_reader.extract_content(pdf_path)
for item in items[:2]:
    print(f"Name: {item.get('name')} | Cx: {item.get('cx', 'none')} | Cy: {item.get('cy', 'none')} | Img: {item.get('images')}")

# Actually, cx and cy are deleted in pdf_reader: `del p["cx"]`
# So we can't see them. But if `test_block_logic` worked, there is a tiny difference.

# Let's check `test_block_logic.py`'s `is_price_line` vs `pdf_reader.py`'s `is_price_line`:
# Also, does `test_block_logic.py` use `blocks` with the same `col` and `merged_text`?
