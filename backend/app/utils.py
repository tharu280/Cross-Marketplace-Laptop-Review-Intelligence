import os
import faiss
import json
import sqlite3
from contextlib import contextmanager
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from . import config
from fastapi import HTTPException

embedding_model_instance = None
faiss_index_instance = None
metadata_store_instance = None
llm_model_instance = None
artifacts_loaded = False


def load_all_artifacts():
    """Loads all models and data required for the RAG system."""
    global embedding_model_instance, faiss_index_instance, metadata_store_instance, llm_model_instance, artifacts_loaded

    if artifacts_loaded:
        print("Artifacts already loaded.")
        return True

    print("Loading all RAG artifacts...")
    all_loaded = True
    try:

        print(f"Loading embedding model: {config.EMBEDDING_MODEL_NAME}...")
        embedding_model_instance = SentenceTransformer(
            config.EMBEDDING_MODEL_NAME)
        print(" > Embedding model loaded.")

        if os.path.exists(config.INDEX_PATH):
            print(f"Loading FAISS index from {config.INDEX_PATH}...")
            faiss_index_instance = faiss.read_index(config.INDEX_PATH)
            print(
                f" > FAISS index loaded ({faiss_index_instance.ntotal} vectors).")
        else:
            print(f"ERROR: FAISS index file not found at {config.INDEX_PATH}")
            all_loaded = False

        if os.path.exists(config.METADATA_PATH):
            print(f"Loading metadata from {config.METADATA_PATH}...")
            with open(config.METADATA_PATH, 'r', encoding='utf-8') as f:
                metadata_store_instance = json.load(f)
            print(
                f" > Metadata loaded ({len(metadata_store_instance)} entries).")
        else:
            print(f"ERROR: Metadata file not found at {config.METADATA_PATH}")
            all_loaded = False

        if config.GOOGLE_API_KEY:
            print("Configuring Google Generative AI client...")
            try:
                genai.configure(api_key=config.GOOGLE_API_KEY)
                llm_model_instance = genai.GenerativeModel(
                    config.GEMINI_MODEL_NAME)

                print(
                    f" > Google client configured for model '{config.GEMINI_MODEL_NAME}'.")
            except Exception as e:
                print(f"ERROR: Failed to configure Google client: {e}")
                all_loaded = False
        else:
            print("ERROR: GOOGLE_API_KEY is missing. Cannot configure LLM.")
            all_loaded = False

        if not os.path.exists(config.DB_PATH):
            print(f"ERROR: SQLite DB file not found at {config.DB_PATH}")
            all_loaded = False
        else:
            print(f" > SQLite DB file found at {config.DB_PATH}.")

    except Exception as e:
        print(f"FATAL ERROR during artifact loading: {e}")
        all_loaded = False

    artifacts_loaded = all_loaded
    if artifacts_loaded:
        print("\n All artifacts loaded successfully! ")
    else:
        print("\n  ❌ CRITICAL ERROR: Failed to load one or more artifacts. API may not function correctly.")

    return artifacts_loaded


@contextmanager
def get_db_connection():
    """Provides a managed database connection to the dynamic DB."""
    conn = None
    if not os.path.exists(config.DB_PATH):
        print(f"ERROR: Database file not found at {config.DB_PATH}")
        raise FileNotFoundError(f"Database file not found at {config.DB_PATH}")

    try:
        conn = sqlite3.connect(config.DB_PATH)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")

        raise HTTPException(
            status_code=500, detail=f"Database connection error: {e}")
    except Exception as e:
        print(f"Unexpected error getting DB connection: {e}")
        raise HTTPException(
            status_code=500, detail=f"Unexpected DB error: {e}")
    finally:
        if conn:
            conn.close()


def get_dynamic_data_for_sku(sku: str):
    """Fetches latest price, rating, availability etc. for a given SKU from SQLite."""
    dynamic_info = {"latest_price": "N/A", "avg_rating": "N/A",
                    "availability": "N/A", "shipping_eta": "N/A", "vendor": "N/A"}
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT price, date, vendor_name, promo_badges
                FROM PriceHistory WHERE laptop_sku = ? ORDER BY date DESC LIMIT 1
            """, (sku,))
            latest_price_row = cursor.fetchone()

            cursor.execute("""
                SELECT currency, average_rating, review_count, availability, shipping_eta
                FROM Laptop WHERE sku = ?
            """, (sku,))
            laptop_row = cursor.fetchone()

            if laptop_row:
                dynamic_info[
                    "avg_rating"] = f"{laptop_row['average_rating']:.1f}/5.0 ({laptop_row['review_count']} reviews)"
                dynamic_info["availability"] = laptop_row['availability']
                dynamic_info["shipping_eta"] = laptop_row['shipping_eta']
                currency = laptop_row['currency']
            else:
                print(
                    f"Warning: Laptop details not found in DB for SKU: {sku}")
                currency = "Unknown Currency"

            if latest_price_row:
                dynamic_info["latest_price"] = f"{currency} {latest_price_row['price']:.2f}"
                if latest_price_row['promo_badges'] and latest_price_row['promo_badges'].lower() != "none":
                    dynamic_info["latest_price"] += f" ({latest_price_row['promo_badges']})"
                dynamic_info["vendor"] = latest_price_row['vendor_name'] if latest_price_row['vendor_name'] else "N/A"
            else:
                print(f"Warning: No price history found in DB for SKU: {sku}")

    except sqlite3.Error as e:

        print(f"SQLite error fetching dynamic data for SKU '{sku}': {e}")
    except Exception as e:

        print(f"Unexpected error fetching dynamic data for SKU '{sku}': {e}")

    return dynamic_info
