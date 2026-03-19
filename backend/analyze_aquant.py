import fitz
import re
import json

pdf_path = r"uploads\Aquant Price List Vol 15. Feb 2026_Searchable.pdf"
doc = fitz.open(pdf_path)

# Extract text from first 15 pages
print("=" * 100)
print("AQUANT PDF STRUCTURE ANALYSIS - First 15 Pages")
print("=" * 100)

samples = []
for page_num in range(min(15, len(doc))):
    page = doc[page_num]
    text = page.get_text()
    
    print(f"\n\n{'='*100}")
    print(f"PAGE {page_num + 1}")
    print(f"{'='*100}\n")
    
    # Print first 60 lines
    lines = text.split('\n')[:60]
    for line in lines:
        if line.strip():
            print(line)
            # Look for color patterns
            if re.search(r'(WHITE|BLACK|RED|BLUE|GREEN|GRAY|BEIGE|CHROME|GOLD|SILVER|CP|WH|BK|RD|BL|GR)', line, re.IGNORECASE):
                if not any(s in line for s in samples):
                    samples.append(line.strip())

print("\n\n" + "=" * 100)
print("COLOR CODE PATTERNS FOUND:")
print("=" * 100)
for sample in samples[:50]:
    print(sample)

doc.close()
