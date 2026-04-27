import search_engine

search_engine.load_index()

print("=== Searching '1333 BM' ===")
results = search_engine.search("1333 BM")
for r in results[:5]:
    print(f"  {r.get('search_code','')} | images={r.get('images',[])} | name={r.get('name','')[:60]}")

print()
print("=== Searching '11333 LM' ===")
results2 = search_engine.search("11333 LM")
for r in results2[:5]:
    print(f"  {r.get('search_code','')} | images={r.get('images',[])} | name={r.get('name','')[:60]}")

print()
print("=== Searching '1333' (family) ===")
results3 = search_engine.search("1333")
for r in results3[:7]:
    print(f"  {r.get('search_code','')} | images={r.get('images',[])} | name={r.get('name','')[:60]}")
