import os
from dotenv import load_dotenv


load_dotenv()

print("Attempting to load environment variables...")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

BACKEND_DIR = '/Users/dilshantharushika/Desktop/laptop agent/backend'
INDEX_PATH = '/Users/dilshantharushika/Desktop/laptop agent/backend/laptops.index'
METADATA_PATH = '/Users/dilshantharushika/Desktop/laptop agent/backend/laptops_metadata.json'
DB_PATH = '/Users/dilshantharushika/Desktop/laptop agent/backend/laptops_dynamic.db'


EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
GEMINI_MODEL_NAME = 'gemini-2.5-flash'


if GOOGLE_API_KEY:
    print("GOOGLE_API_KEY loaded successfully.")
else:
    print("WARNING: GOOGLE_API_KEY not found in .env file or environment variables.")

print(f"Index Path: {INDEX_PATH}")
print(f"Metadata Path: {METADATA_PATH}")
print(f"DB Path: {DB_PATH}")
