import os
import json
import glob
import pandas as pd

# Directory containing all quote JSON files
QUOTES_DIR = os.path.join(os.path.dirname(__file__), 'quotes_history')
STATIC_IMG_DIR = os.path.join(os.path.dirname(__file__), 'static', 'images')

rows = []
for file in glob.glob(os.path.join(QUOTES_DIR, '*.json')):
    with open(file, encoding='utf-8') as f:
        try:
            data = json.load(f)
        except Exception as e:
            continue
        for item in data.get('items', []):
            name = item.get('name') or ''
            image = item.get('image') or ''
            brand = ''
            # Brand detection (simple)
            if 'aquant' in image.lower() or 'aquant' in name.lower():
                brand = 'Aquant'
            elif 'kohler' in image.lower() or 'kohler' in name.lower() or name.strip().upper().startswith('K-'):
                brand = 'Kohler'
            if brand:
                note = ''
                if not image:
                    note = 'Missing image path'
                else:
                    img_path = image.replace('/', os.sep).lstrip(os.sep)
                    abs_img_path = os.path.join(os.path.dirname(__file__), img_path)
                    if not os.path.exists(abs_img_path):
                        note = 'Image file not found'
                rows.append({'Product Name': name, 'Brand': brand, 'Image Path': image, 'Note': note})

# Save report
report_path = os.path.join(os.path.dirname(__file__), 'quotes_image_report.csv')
df = pd.DataFrame(rows)
df.to_csv(report_path, index=False, encoding='utf-8')
print(f'Report generated: {report_path}')
print(f'Total products checked: {len(rows)}')
print(df.head(10))
