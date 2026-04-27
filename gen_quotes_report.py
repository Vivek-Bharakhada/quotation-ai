import os, json, pandas as pd 
from glob import glob 
report = [] 
image_dir = 'static/images' 
for file in glob('backend/quotes_history/*.json'): 
    with open(file, 'r', encoding='utf-8') as f: 
        try: 
            data = json.load(f) 
        except Exception as e: 
            continue 
        for item in data: 
            name = item.get('name', '') 
            product = item.get('product', '') 
            image = item.get('image', '') 
            note = '' 
            if product in ['Aquant', 'Kohler']: 
                if not image or image.lower() in ['placeholder', 'null', 'none']: 
                    note = 'Missing or placeholder image' 
                elif not os.path.isfile(os.path.join(image_dir, image)): 
                    note = 'Image not found in static/images' 
                report.append({'Product Name': name, 'Image Path': image, 'Note': note}) 
pd.DataFrame(report).to_csv('quotes_report.csv', index=False) 
df = pd.DataFrame(report) 
print(df.head(20).to_string(index=False))
print(type(item), item)  
