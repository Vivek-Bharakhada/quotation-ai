import sys
import os

# Add backend to path to import search_engine
sys.path.append('.')
import search_engine

# Load existing index
search_engine.load_index()

new_products = [
    {
        "text": "1003 G - Gold\nBrass Bottle Trap\nSize : 32 mm With 300 mm Long Pipe\nMRP : ₹ 7,500/-",
        "name": "1003 G - Gold",
        "price": "7500",
        "images": ["/static/images/manual/gold_trap.png"],
        "brand": "Aquant",
        "category": "Bottle Trap",
        "source": "Manual Entry"
    },
    {
        "text": "450-1003 G - Gold\nBottle Trap Pipe\nSize : 450 mm\nMRP : ₹ 3,250/-",
        "name": "450-1003 G - Gold",
        "price": "3250",
        "images": ["/static/images/manual/gold_trap.png"],
        "brand": "Aquant",
        "category": "Bottle Trap",
        "source": "Manual Entry"
    }
]

# Add to index
search_engine.add_to_index(None, new_products)
search_engine.save_index()

print(f"Successfully added {len(new_products)} products to the index.")
