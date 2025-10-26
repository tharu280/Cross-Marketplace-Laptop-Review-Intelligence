from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import sqlite3
from . import utils
from . import config
from . import rag_handler
from .models import (
    ChatQuery, ChatResponse, Laptop, PriceRecord, ReviewRecord, QARecord, ChatMessage
)


app_startup_success = utils.load_all_artifacts()


app = FastAPI(
    title="Laptop Insights API",
    description="API for querying laptop specs (static), dynamic data (price, reviews), and a RAG chatbot.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Simple root endpoint to check if the API is running."""
    return {"message": "Welcome to the Laptop Insights API. Visit /docs for documentation."}


@app.get("/api/v1/laptops", response_model=List[Laptop], tags=["Catalog", "Search & Filtering"])
def get_laptops(  # This is the CORRECT definition with filters
    brand: Optional[str] = None,          # e.g., ?brand=Lenovo
    min_rating: Optional[float] = None,   # e.g., ?min_rating=4.0
    availability: Optional[str] = None    # e.g., ?availability=In Stock
):
    """
    Fetches the list of laptops from the catalog, optionally filtering by
    brand, minimum average rating, and availability.
    """
    laptops_data = []
    query = """
        SELECT sku, brand, model_name, currency, availability,
               shipping_eta, review_count, average_rating
        FROM Laptop
    """
    conditions = []
    params = []

    if brand:
        conditions.append("LOWER(brand) = LOWER(?)")
        params.append(brand)
    if min_rating is not None:
        if 0.0 <= min_rating <= 5.0:
            conditions.append("average_rating >= ?")
            params.append(min_rating)
        else:
            raise HTTPException(
                status_code=400, detail="min_rating must be between 0.0 and 5.0")
    if availability:
        conditions.append("LOWER(availability) = LOWER(?)")
        params.append(availability)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    print(f"Executing Query: {query}")  # For debugging
    print(f"Parameters: {params}")     # For debugging

    try:
        with utils.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            laptops_data = [Laptop(**row) for row in rows]
            print(f"Found {len(laptops_data)} laptops matching filters.")
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500, detail=f"Database file not found: {e}")
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Database query error: {e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}")

    return laptops_data


@app.get("/api/v1/laptops/{sku}/price-history", response_model=List[PriceRecord], tags=["Dynamic Data"])
def get_price_history(sku: str):
    """Fetches the price history for a specific laptop SKU."""
    prices = []
    try:
        with utils.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM Laptop WHERE sku = ?", (sku,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=404, detail=f"Laptop SKU '{sku}' not found in catalog.")

            cursor.execute(
                "SELECT id, laptop_sku, price, date, vendor_name, promo_badges FROM PriceHistory WHERE laptop_sku = ? ORDER BY date DESC",
                (sku,)
            )
            rows = cursor.fetchall()
            prices = [PriceRecord(**row) for row in rows]
            if not prices:
                print(f"No price history found for SKU: {sku}")
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500, detail=f"Database file not found: {e}")
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Database query error: {e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}")
    return prices


@app.get("/api/v1/laptops/{sku}/reviews", response_model=List[ReviewRecord], tags=["Dynamic Data"])
def get_reviews(sku: str):
    """Fetches the reviews for a specific laptop SKU."""
    reviews = []
    try:
        with utils.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM Laptop WHERE sku = ?", (sku,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=404, detail=f"Laptop SKU '{sku}' not found.")

            cursor.execute(
                "SELECT id, laptop_sku, rating, review_text, date, source FROM Review WHERE laptop_sku = ? ORDER BY date DESC",
                (sku,)
            )
            rows = cursor.fetchall()
            reviews = [ReviewRecord(**row) for row in rows]
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500, detail=f"Database file not found: {e}")
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Database query error: {e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}")
    return reviews


@app.get("/api/v1/laptops/{sku}/qanda", response_model=List[QARecord], tags=["Dynamic Data"])
def get_qanda(sku: str):
    """Fetches the Q&A for a specific laptop SKU."""
    qanda = []
    try:
        with utils.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM Laptop WHERE sku = ?", (sku,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=404, detail=f"Laptop SKU '{sku}' not found.")

            cursor.execute(
                "SELECT id, laptop_sku, question_text, answer_text, date, source FROM QuestionAnswer WHERE laptop_sku = ? ORDER BY date DESC",
                (sku,)
            )
            rows = cursor.fetchall()
            qanda = [QARecord(**row) for row in rows]
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500, detail=f"Database file not found: {e}")
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Database query error: {e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {e}")
    return qanda


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["RAG Chat & Recommender"])
async def post_chat(request: ChatQuery):
    """Handles chat requests using the RAG pipeline."""
    if not app_startup_success:
        raise HTTPException(
            status_code=503,
            detail="API failed to load necessary models or data files on startup. Check server logs."
        )

    try:

        result = rag_handler.get_rag_response(
            query=request.query,
            history=request.history
        )

        return ChatResponse(**result)

    except Exception as e:
        print(f"Error processing chat request: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {e}"
        )
