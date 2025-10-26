Cross-Marketplace Laptop & Review Intelligence Engine

This project builds an insights engine for specific business laptops sold on Lenovo and HP first-party stores, fulfilling the requirements of the “Cross-Marketplace Laptop & Review Intelligence” assignment.
It leverages Retrieval-Augmented Generation (RAG) to combine canonical technical specifications from PDFs with mutable data (price, reviews, availability) scraped or manually entered from brand websites — enabling interactive analytics and a chatbot interface.

🚩 Problem Statement

Create a system that can:

Answer natural-language questions about laptop specifications.

Provide purchase recommendations with verifiable citations.

Offer analytical insights about four business laptops:

Lenovo ThinkPad E14 Gen 5 (⁠Intel⁠)

Lenovo ThinkPad E14 Gen 5 (⁠AMD⁠)

HP ProBook 450 G10

HP ProBook 440 G11

Sources:

PDF spec sheets → immutable ground truth.

Brand product pages → dynamic data (price, reviews, availability).

✨ Features

Coherent Dataset: Combines static PDF specs with dynamic marketplace data.

RAG Chatbot: Answers questions using Google Gemini with source citations.

Laptop Recommender: Suggests models based on budget/spec constraints.

Interactive Exploration: Streamlit UI for filtering, browsing, and comparisons.

Reviews Intelligence: Charts for review trends and rating distributions.

Versioned REST API: Modular FastAPI backend with /docs auto-documentation.

Source Linking: Links to official PDF specification sheets.

🧩 Tech Stack
Component	Technology
Backend	Python · FastAPI · Uvicorn
Frontend	Streamlit
LLM	Google Gemini API (gemini-1.5-flash)
Vector Search	FAISS (faiss-cpu)
Embeddings	Sentence Transformers (all-MiniLM-L6-v2)
Database	SQLite
Data Manipulation & Charts	Pandas · Plotly Express
API Calls	Requests
Environment	Conda
Config	python-dotenv
⚙️ Architecture Overview

The system employs a Retrieval-Augmented Generation (RAG) pipeline combining:

Static data (technical specs → PDF-derived JSON)

Dynamic data (market info → SQLite)

LLM reasoning (Gemini API)

Vector retrieval (FAISS)

📘 Static Data Pipeline — Technical Specifications

Source:
4 official PDF spec sheets (Lenovo × 2 · HP × 2).

Processing & Chunking:
Text extracted and manually segmented into semantic sections (“Processor”, “Memory”, “Ports”, etc.) → structured as JSON.

JSON Schema:

{
  "section_title": "Processor",
  "content": "Up to Intel Core i7...",
  "subfeatures": ["Intel Core i5", "Intel Core i7"],
  "source_model": "ThinkPad E14 Gen 5 (Intel)",
  "source_citations": [12, 13]
}


Embedding & Indexing:

Embeddings → Sentence Transformer (all-MiniLM-L6-v2, 384 dims)

Stored in FAISS IndexFlatL2 (backend/laptops.index)

Metadata parallel JSON → backend/laptops_metadata.json

Each vector ↔ metadata record (content, sku, section_title, citations).

📊 Dynamic Data Pipeline — Market Information

Source:
Manual / synthetic data from Lenovo + HP product pages (price, availability, reviews).

Storage: SQLite (backend/laptops_dynamic.db)

Schema Overview:

Table	Purpose
Laptop	Brand, model, availability, rating, currency
PriceHistory	Price points + dates + vendor
Review	Individual reviews (rating, text, date)
QuestionAnswer	User Q&A entries

All linked via sku ↔ source_model.

🧠 Backend API — FastAPI

Structure:

backend/app/
├── config.py          # Env vars, API key loading
├── main.py            # FastAPI app + endpoints
├── models.py          # Pydantic response/request models
├── rag_handler.py     # Core RAG logic
└── utils.py           # FAISS, metadata, DB, Gemini helpers


RAG Flow:

Embed user query.

Search FAISS index → relevant spec chunks.

Retrieve metadata + citations.

Identify related SKUs.

Query SQLite for dynamic data.

Compose prompt → Gemini API (including static + dynamic context).

Return LLM response + citations.

Docs:
Auto-generated via FastAPI → /docs

🖥️ Frontend UI — Streamlit

File: streamlit_app.py
Features:

Chat interface with session history (last 5 messages).

Fetches data via HTTP → FastAPI endpoints (never touches DB directly).

Filter laptops by brand/rating/availability.

Interactive price & review charts (via Plotly Express).

📁 Project Structure
/laptop-agent
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── rag_handler.py
│   │   └── utils.py
│   ├── .env              # API key (not committed)
│   ├── .env.example      # Template
│   ├── laptops.index
│   ├── laptops_metadata.json
│   ├── laptops_dynamic.db
│   └── requirements.txt
├── data/                 # Source JSONs from PDFs
├── scripts/
│   ├── build_vector_index.ipynb / .py
│   └── setup_dynamic_db.ipynb  / .py
├── streamlit_app.py
├── schema_diagram.png
├── .gitignore
└── README.md

🚀 Setup & Run Instructions
1️⃣ Prerequisites

Python ≥ 3.9

Conda

Git

2️⃣ Clone the Repository
git clone https://github.com/<your-github-username>/<your-repo-name>.git
cd <your-repo-name>

3️⃣ Create & Activate Environment
conda create --name AgentInbox python=3.10 -y
conda activate AgentInbox

4️⃣ Install Dependencies

Backend:

cd backend
pip install -r requirements.txt


Frontend:

cd ..
pip install streamlit pandas plotly requests

5️⃣ Set Environment Variables
cd backend
cp .env.example .env
# then edit .env:
GOOGLE_API_KEY=your_actual_google_api_key_here

6️⃣ Generate Data Artifacts

Dynamic Database:

python scripts/setup_dynamic_db.py
# or run: scripts/setup_dynamic_db.ipynb


FAISS Index:

python scripts/build_vector_index.py
# or run: scripts/build_vector_index.ipynb


Ensure PDF-derived JSON files exist in /data.

7️⃣ Run Backend API
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

8️⃣ Run Frontend UI

Open a new terminal:

cd laptop-agent
conda activate AgentInbox
streamlit run streamlit_app.py


Then visit:
👉 http://localhost:8501

✅ You’re Ready!

FastAPI → http://localhost:8000/docs

Streamlit → http://localhost:8501
