import fitz
import os

PDF_PATH = r"c:\Movies\quotation-ai\quotation-ai\backend\uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"

def find_pages(codes):
    doc = fitz.open(PDF_PATH)
    results = {}
    for code in codes:
        pages = []
        for i, page in enumerate(doc):
            if code in page.get_text():
                pages.append(i)
        results[code] = pages
    return results

if __name__ == "__main__":
    res = find_pages(["2750", "2744"])
    print(res)
