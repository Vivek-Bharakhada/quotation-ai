import fitz
import os
import re

pdf_path = r"c:\Movies\quotation-ai\quotation-ai\backend\uploads\Kohler_Pricebook (March'26).pdf"
if os.path.exists(pdf_path):
    doc = fitz.open(pdf_path)
    count = 0
    for page_num in range(min(100, len(doc))):
        page = doc[page_num]
        text = page.get_text("text")
        # Regex for K- code followed by slash and another K- code
        matches = re.findall(r'K\s*-\s*[A-Z0-9-]+\s*/\s*K\s*-\s*[A-Z0-9-]+', text)
        if matches:
            print(f"--- Page {page_num} ---")
            for m in matches:
                print(m)
            count += 1
            if count > 10: break
    doc.close()
else:
    print("PDF not found")
