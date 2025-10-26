
Cross-Marketplace Laptop & Review Intelligence Engine

This project builds an insights engine for specific business laptops sold on Lenovo and HP first-party stores, fulfilling the requirements of the "Cross-Marketplace Laptop & Review Intelligence" assignment. It leverages Retrieval-Augmented Generation (RAG) to combine canonical technical specifications from PDFs with mutable data (like price and reviews) scraped or manually entered from brand websites, providing an interactive analytics experience and a chatbot interface.

Problem Statement

The goal is to create a system that can answer natural language questions, provide purchase recommendations with citations, and offer analytical insights about four specific business laptops (Lenovo ThinkPad E14 Gen 5 Intel/AMD, HP ProBook 450 G10, HP ProBook 440 G11). The system must treat official PDF spec sheets as ground truth for technical details and brand product pages as the source for dynamic information like price, availability, and reviews.

Features

Coherent Dataset: Integrates static technical specs with dynamic market data (prices, reviews, availability, etc.).

RAG Chatbot: Answers natural language questions about laptop specs, prices, availability, and comparisons using Google Gemini, providing citations from source PDFs. Supports chat history (last 5 messages).

Laptop Recommender: Suggests suitable laptop models based on user constraints (budget, specs, availability) provided via the chat interface, with rationales and citations.

Interactive Exploration & Comparison: A Streamlit UI allows users to browse the laptop catalog, apply filters (brand, rating, availability), and view detailed information including price trends and recent reviews.

Reviews Intelligence: Visualizes review volume and rating trends over time, plus rating distributions for selected laptops.

Versioned REST API: A modular FastAPI backend exposes endpoints for catalog, filtering, price history, reviews, Q&A, and the RAG chat/recommendation service. Includes automatically generated documentation via /docs.

Source Linking: Provides links back to the original canonical PDF spec sheets.

Tech Stack

Backend: Python, FastAPI, Uvicorn

Frontend: Streamlit

LLM: Google Gemini API (gemini-1.5-flash via google-generativeai)

Vector Database/Search: FAISS (faiss-cpu)

Embeddings: Sentence Transformers (all-MiniLM-L6-v2)

Dynamic Data Storage: SQLite

Data Manipulation & Charting: Pandas, Plotly Express

API Interaction: Requests

Environment Management: Conda

Configuration: python-dotenv

Architecture & Design Decisions

The system employs a Retrieval-Augmented Generation (RAG) architecture to provide accurate, context-aware answers based on both static and dynamic data sources.

Static Data Pipeline (Technical Specifications)

Source: The 4 provided PDF spec sheets were treated as the immutable ground truth for technical details.

Processing & Chunking: To prepare the PDFs for semantic search, the text content was extracted and manually segmented into logical chunks based on the sections within the documents (e.g., "Processor", "Memory", "Ports and Slots", "Display"). Each chunk was structured into a JSON object.

JSON Structure & Metadata: Each JSON object represents a semantic chunk and includes:

content: The primary text content of the section.

subfeatures (optional): A list of specific sub-points or options within that section, each with its own content.

source_model (sku): A unique identifier linking the chunk back to the specific laptop model (e.g., "ThinkPad E14 Gen 5 (Intel)"). This serves as the crucial link to dynamic data.

section_title: The heading of the section (e.g., "Processor").

source_citations: A list of citation numbers extracted directly from the PDF text associated with the chunk. This metadata is essential for providing verifiable answers.
These structured JSON files form the static "generated dataset" artifact (/data folder).

Embedding & Indexing:

The content from each main section and subfeature in the JSON files was extracted.

The SentenceTransformer library (with the all-MiniLM-L6-v2 model) was used to convert each text chunk into a 384-dimensional vector embedding.

These embeddings were stored in a FAISS index (laptops.index). IndexFlatL2 was chosen for its 100% retrieval accuracy, which is crucial for grounding the LLM in the correct technical facts, and feasible given the relatively small number of chunks.

The corresponding metadata (text chunk, sku, section title, citations) for each vector was stored in a separate JSON list (laptops_metadata.json), maintaining a parallel structure where the metadata at index i corresponds to the vector at index i in the FAISS file.

Dynamic Data Pipeline (Market Information)

Source: The assignment specifies using live brand product pages (Lenovo/HP) for mutable data (price, availability, reviews, Q&A, etc.). For this prototype, this data was manually collected (or generated synthetically via script) as web scraping can be complex and fragile.

Storage: SQLite was chosen for its simplicity as a file-based database, suitable for a prototype. The database (laptops_dynamic.db) contains tables:

Laptop: Stores the main catalog info (brand, model name) and the current snapshot of mutable data (availability, review count, average rating, currency, shipping ETA). The primary key is sku, matching the source_model from the static metadata.

PriceHistory: Stores historical price points with date, vendor, and promo badges, linked via laptop_sku.

Review: Stores individual reviews with rating, text, date, and source, linked via laptop_sku.

QuestionAnswer: Stores Q&A excerpts, linked via laptop_sku.

Linking: The sku column in the Laptop table (matching source_model in laptops_metadata.json) acts as the foreign key, connecting the dynamic market data to the static technical specifications.

Backend API (FastAPI)

A modular structure (/app directory) was used to separate concerns (configuration, utilities, RAG logic, API endpoints).

utils.py handles loading all artifacts (FAISS index, metadata, embedding model, LLM client) once on application startup for efficiency. It also provides the database connection context manager (get_db_connection) and the function to query dynamic data (get_dynamic_data_for_sku).

rag_handler.py contains the core get_rag_response function. When called by the /chat endpoint:

It embeds the user's current query using the loaded Sentence Transformer.

It searches the loaded FAISS index for relevant static spec chunks (retrieving indices).

It looks up the corresponding text and citation metadata from the loaded metadata store using the indices.

It identifies the unique SKUs mentioned in the retrieved static chunks.

It calls utils.get_dynamic_data_for_sku to query the SQLite database for current price, rating, availability, etc., for those SKUs.

It constructs a detailed prompt for the Google Gemini API, including:

System instructions (role, constraints, citation rules).

The retrieved static spec chunks (with citations).

The retrieved dynamic data (price, rating, availability).

The recent chat history (last 5 messages).

The user's current query.

It calls the Gemini API via the configured client (google-generativeai). Safety settings are adjusted to prevent overly sensitive blocking for technical content.

It returns the LLM's generated answer and the list of retrieved static context chunks.

API endpoints in main.py handle incoming HTTP requests, call the appropriate database query functions (via utils.py) or the RAG handler, and return structured JSON responses using Pydantic models.

FastAPI automatically generates OpenAPI documentation available at the /docs route.

Frontend UI (Streamlit)

streamlit_app.py creates the user interface.

It interacts only with the FastAPI backend via HTTP requests (using the requests library) to fetch data and get chat responses. It does not directly access the database or models.

It uses st.session_state to manage chat history locally within the user's browser session.

Pandas and Plotly Express are used to process and display the price and review trend charts based on data fetched from the API.





Project Structure/laptop agent
|-- /backend
|   |-- /app
|   |   |-- __init__.py
|   |   |-- config.py       # Configuration, .env loading
|   |   |-- main.py         # FastAPI app, API endpoints
|   |   |-- models.py       # Pydantic models
|   |   |-- rag_handler.py  # Core RAG logic
|   |   `-- utils.py        # Model/data loading, DB connection
|   |-- .env              # <-- DO NOT COMMIT (Contains API Key)
|   |-- .env.example      # <-- Commit this (Template for .env)
|   |-- laptops.index     # FAISS index file
|   |-- laptops_metadata.json # Static spec metadata
|   |-- laptops_dynamic.db  # SQLite database
|   `-- requirements.txt  # Backend dependencies
|-- /data
|   `-- *.json            # Source JSONs derived from PDFs
|-- /scripts
|   |-- build_vector_index.ipynb # Notebook to create FAISS index/metadata (or .py)
|   `-- setup_dynamic_db.ipynb   # Notebook to create/seed SQLite DB (or .py)
|-- .gitignore            # Files/folders for Git to ignore
|-- README.md             # This file
|-- schema_diagram.png    # <-- Add your exported schema diagram image here
`-- streamlit_app.py    # Streamlit frontend application
Setup and Run InstructionsPrerequisites:Python (>= 3.9 recommended)Conda (for environment management)GitSteps:Clone the Repository:git clone [https://github.com/](https://github.com/)<your-github-username>/<your-repo-name>.git
cd <your-repo-name>
Set Up Conda Environment:# Create and activate the environment (using the same name as development)
conda create --name AgentInbox python=3.10 -y
conda activate AgentInbox
(Adjust Python version if needed)Install Dependencies:Navigate to the backend directory:cd backend
Install backend requirements:pip install -r requirements.txt
Navigate back to the project root:cd ..
Install frontend requirements:pip install streamlit pandas plotly requests # Ensure these are installed
Set Up Environment Variables:Navigate to the backend directory:cd backend
Copy the example file:cp .env.example .env
Edit the .env file and replace the placeholder with your actual Google Gemini API Key:# backend/.env
GOOGLE_API_KEY=your_actual_google_api_key_here
Generate Data Artifacts (if not included or need regeneration):Run the dynamic database setup (creates backend/laptops_dynamic.db):# From the project root directory:
python scripts/setup_dynamic_db.py
# OR run the setup_dynamic_db.ipynb notebook
Run the FAISS index creation (creates backend/laptops.index and backend/laptops_metadata.json):# From the project root directory:
python scripts/build_vector_index.py
# OR run the build_vector_index.ipynb notebook
(Ensure the source JSON files derived from PDFs are present in the /data directory if running the index script)Run the Backend API:Navigate to the backend directory:cd backend
Start the Uvicorn server:uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Keep this terminal running.Run the Frontend UI:Open a new terminal window.Navigate to the project root directory (/laptop agent).Activate the Conda environment:conda activate AgentInbox
Run the Streamlit app:streamlit run streamlit_app.py

