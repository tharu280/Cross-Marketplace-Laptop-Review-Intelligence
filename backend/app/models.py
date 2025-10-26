from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class ChatMessage(BaseModel):
    role: str = Field(..., example="user")
    content: str = Field(...,
                         example="What processors does the Intel E14 have?")


class ChatQuery(BaseModel):
    query: str = Field(..., example="What about the AMD version?")

    history: Optional[List[ChatMessage]] = Field(None, example=[
        {"role": "user", "content": "What processors does the Intel E14 have?"},
        {"role": "model",
            "content": "The ThinkPad E14 Gen 5 (Intel) offers various 13th Gen Intel Core processors..."}
    ])


class RetrievedChunk(BaseModel):
    sku: str
    text: str
    section_title: Optional[str] = None
    citations: List[int] = []


class ChatResponse(BaseModel):
    llm_answer: str
    # for debugging
    retrieved_context: List[RetrievedChunk]


class Laptop(BaseModel):
    sku: str
    brand: str
    model_name: str
    currency: Optional[str] = None
    availability: Optional[str] = None
    shipping_eta: Optional[str] = None
    review_count: Optional[int] = None
    average_rating: Optional[float] = None


class PriceRecord(BaseModel):
    id: int
    laptop_sku: str
    price: float
    date: date
    vendor_name: Optional[str] = None
    promo_badges: Optional[str] = None


class ReviewRecord(BaseModel):
    id: int
    laptop_sku: str
    rating: int
    review_text: Optional[str] = None
    date: date
    source: Optional[str] = None


class QARecord(BaseModel):
    id: int
    laptop_sku: str
    question_text: str
    answer_text: Optional[str] = None
    date: date
    source: Optional[str] = None
