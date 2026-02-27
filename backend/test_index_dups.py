import json
import os

pdf_path = r'c:\Users\DELL\OneDrive\Desktop\AIML Project\quotation-ai\backend\search_index_v2.json'
data = json.load(open(pdf_path, 'r', encoding='utf-8'))
for item in data.get('items', []):
    name = item.get('name', '')
    if '9273' in name or '9274' in name:
        print(f"Name: {name} | Images: {item.get('images', [])}")
