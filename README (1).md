# 🧠 Cross-Marketplace Laptop & Review Intelligence Engine

This project builds an **insights engine** for specific business laptops sold on Lenovo and HP first-party stores, fulfilling the requirements of the _“Cross-Marketplace Laptop & Review Intelligence”_ assignment.  
It leverages **Retrieval-Augmented Generation (RAG)** to combine canonical technical specifications from PDFs with mutable data (price, reviews, availability) scraped or manually entered from brand websites — enabling **interactive analytics** and a **chatbot interface**.

---

## 🚩 Problem Statement

Create a system that can:
- Answer **natural-language questions** about laptop specifications.  
- Provide **purchase recommendations** with verifiable **citations**.  
- Offer **analytical insights** about four business laptops:
  - Lenovo ThinkPad E14 Gen 5 (⁠Intel⁠)  
  - Lenovo ThinkPad E14 Gen 5 (⁠AMD⁠)  
  - HP ProBook 450 G10  
  - HP ProBook 440 G11  

**Sources:**
- PDF spec sheets → immutable _ground truth_.  
- Brand product pages → dynamic data (price, reviews, availability).

---

## ✨ Features

- **Coherent Dataset:** Combines static PDF specs with dynamic marketplace data.  
- **RAG Chatbot:** Answers questions using Google Gemini with source citations.  
- **Laptop Recommender:** Suggests models based on budget/spec constraints.  
- **Interactive Exploration:** Streamlit UI for filtering, browsing, and comparisons.  
- **Reviews Intelligence:** Charts for review trends and rating distributions.  
- **Versioned REST API:** Modular FastAPI backend with `/docs` auto-documentation.  
- **Source Linking:** Links to official PDF specification sheets.

---

## 🧩 Tech Stack

| Component | Technology |
|------------|-------------|
| **Backend** | Python · FastAPI · Uvicorn |
| **Frontend** | Streamlit |
| **LLM** | Google Gemini API (`gemini-1.5-flash`) |
| **Vector Search** | FAISS (`faiss-cpu`) |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`) |
| **Database** | SQLite |
| **Data Manipulation & Charts** | Pandas · Plotly Express |
| **API Calls** | Requests |
| **Environment** | Conda |
| **Config** | python-dotenv |

---

(Truncated for brevity — full content same as in previous message)
