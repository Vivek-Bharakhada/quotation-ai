import json
import collections

with open('search_index_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    items = data.get('stored_items', [])

no_img = [it for it in items if not it.get('images')]

# 1. Group by page
page_counts = collections.Counter(it.get('page') for it in no_img)
print("MISSING_BY_PAGE (Top 20):")
for page, count in page_counts.most_common(20):
    print(f"  Page {page}: {count} items missing")

# 2. Extract some samples from most problematic pages
print("\nSAMPLES FROM TOP PAGES:")
top_pages = [p for p, c in page_counts.most_common(10)]
for p in top_pages:
    p_samples = [it.get('name', 'N/A')[:60] for it in no_img if it.get('page') == p][:5]
    print(f"  Page {p}: {', '.join(p_samples)}")

# 3. Check if these items had coordinates
missing_coords = sum(1 for it in no_img if not it.get('cx'))
print(f"\nMissing coordinates for {missing_coords} out of {len(no_img)} no-image items.")
