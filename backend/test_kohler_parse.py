import fitz
import sys

def test_kohler(page_nums):
    doc = fitz.open("backend/uploads/Kohler_PriceBook_Nov'25 Edition (1).pdf")
    for page_num in page_nums:
        print(f"--- PAGE {page_num} ---")
        page = doc[page_num]
        
        # Print basic text blocks
        blocks = page.get_text("blocks")
        for b in blocks:
            x0, y0, x1, y1 = b[:4]
            text = b[4].strip()
            print(f"y0: {y0:.1f}, x0: {x0:.1f} | TEXT: {text!r}")
            
test_kohler([4, 5, 8, 9])
