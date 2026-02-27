import os, sys
sys.path.insert(0, '.')
import search_engine

search_engine.load_index()
results = search_engine.search("9272")
print(f"Results: {len(results)}")
for r in results[:5]:
    print(f"Name: {r['name']}, Images: {r['images']}")
