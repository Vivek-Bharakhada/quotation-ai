import fitz
import re
import os
import sys

# Ensure UTF-8 output
if sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pdf_path = r"uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
doc = fitz.open(pdf_path)

def clean_text(text):
    text = text.replace('\x03', ' ')
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

# Define page range
start_page = 8
end_page = 8

# Analyze pages 60 to 95
for page_num in range(start_page - 1, min(end_page, len(doc))):
    page = doc[page_num]
    print(f"\n--- PAGE {page_num + 1} ---")
    
    # Analyze text blocks
    blocks = page.get_text("blocks")
    for b in blocks:
        text = clean_text(b[4]) # Cleaned text for price detection
        print(f"[{b[0]:.1f}, {b[1]:.1f}, {b[2]:.1f}, {b[3]:.1f}] : {b[4]}") # Print original block text
        if "MRP" in text.upper() or "`" in text or "₹" in text:
            print(f"  >>> PRICE DETECTED: {text}")

doc.close()
