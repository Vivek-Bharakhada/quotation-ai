import search_engine

search_engine.load_index()
query = "K- 26475IN-ER-0"
results = search_engine.get_suggestions(query)
print(f"Suggestions for '{query}': {len(results)}")
for r in results:
    print(f" - {r['text']} | {r['full_name']}")

query2 = "K-26475IN-ER-0"
results2 = search_engine.get_suggestions(query2)
print(f"\nSuggestions for '{query2}': {len(results2)}")
for r in results2:
    print(f" - {r['text']} | {r['full_name']}")
