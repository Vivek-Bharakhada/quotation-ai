import os, sys
sys.path.insert(0, '.')
import search_engine
from main import index_local_catalogs

print("Starting manual indexing...")
index_local_catalogs(force=True)
print("Finished manual indexing.")
