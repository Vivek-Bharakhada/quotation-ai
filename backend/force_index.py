import os
import sys

# Set working directory to backend
os.chdir(os.path.join(os.getcwd(), 'backend'))
sys.path.append(os.getcwd())

import main
import search_engine

# Clear existing index
search_engine.stored_items = []
search_engine.keyword_index = {}

print("--- FORCED RE-INDEXING VIA MAIN ---")
main.index_local_catalogs(force=True)
search_engine.save_index()
print("--- SAVED TO backend/search_index_v2.json ---")
