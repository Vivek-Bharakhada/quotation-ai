import os
import sys
# Add backend to path
sys.path.append(os.path.abspath('backend'))
import pdf_reader
import hashlib
import re

pdf_path = r'backend/uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf'
# Only extract 10 pages for speed
print("Running extract_content...")
content = pdf_reader.extract_content(pdf_path, max_pages=10)

# Check first item to see image path
if content:
    print(f"First item images: {content[0]['images']}")
    
    # Check if file exists
    path = content[0]['images'][0].lstrip('/')
    # path is static/images/...
    full_path = os.path.join('backend', path)
    print(f"Checking full path: {full_path}")
    if os.path.exists(full_path):
        print("FILE EXISTS OK.")
    else:
        print("FILE MISSING!")
