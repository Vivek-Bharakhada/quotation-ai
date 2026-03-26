import os
import hashlib
import re

pdf_path = r'backend/uploads/Aquant Price List Vol 15. Feb 2026_Searchable.pdf'
pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
IMAGE_GENERATION_VERSION = "clip_v3_hd"

pdf_prefix_seed = f"{pdf_name}|{os.path.getsize(pdf_path)}|{int(os.path.getmtime(pdf_path))}|{IMAGE_GENERATION_VERSION}"
pdf_prefix_hash = hashlib.md5(pdf_prefix_seed.encode("utf-8")).hexdigest()[:10]
pdf_prefix_base = re.sub(r'[^a-zA-Z0-9_]', '_', pdf_name)[:16]
pdf_prefix = f"{pdf_prefix_base}_{pdf_prefix_hash}"

print(f"PDF Name: {pdf_name}")
print(f"Prefix: {pdf_prefix}")
