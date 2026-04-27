import fitz
import os

pdf_path = r"c:\Movies\quotation-ai\quotation-ai\backend\uploads\Kohler_Pricebook (March'26).pdf"
if os.path.exists(pdf_path):
    doc = fitz.open(pdf_path)
    # Let's check a few pages that might have tables
    # Often bathrooms/toilets have these tables.
    for page_num in [10, 20, 30, 40, 50, 60]:
        page = doc[page_num]
        text = page.get_text("text")
        print(f"--- Page {page_num} ---")
        # Look for lines with multiple K- codes
        for line in text.splitlines():
            if line.count("K-") >= 2 or "/" in line and "K-" in line:
                print(line)
    doc.close()
else:
    print("PDF not found")
