import urllib.request as r
import urllib.parse as p

cats = [
    "Toilets", "Smart Toilets & Bidet Seats", "1 pc Toilets & Wall Hungs",
    "In-Wall Tanks", "Faceplates", "Mirrors", "Vanities", "Wash Basins",
    "Faucets", "Showering", "Steam", "Shower Enclosures", "Fittings", "Accessories",
    "Vibrant Finishes", "French Gold", "Brushed Bronze", "Rose Gold",
    "Matte Black", "Brushed Rose Gold", "Kitchen Sinks & Faucets",
    "Bathtubs & Bath Fillers", "Commercial Products", "Cleaning Solutions"
]

print("=== KOHLER CATEGORY VERIFICATION ===")
total = 0
for cat in cats:
    url = 'http://localhost:8000/catalog/browse?brand=Kohler&collection=' + p.quote(cat)
    result = r.urlopen(url).read().decode()
    count = result.count('"name"')
    total += count
    status = "OK" if count > 0 else "EMPTY"
    print(f"  [{status}] {cat}: {count} products")

print(f"\nTotal Kohler products across all categories: {total}")
