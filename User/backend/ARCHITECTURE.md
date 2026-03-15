"""
SYSTEM ARCHITECTURE - Aluminum Products Chatbot
================================================

OVERALL ARCHITECTURE DIAGRAM
============================

┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                           │
├─────────────────────────────────────────────────────────────┤
│  CLI Interface       │       REST API (Flask)               │
│  (src/main.py)       │       (src/api/app.py)               │
└──────────┬───────────┴──────────────┬──────────────────────┘
           │                          │
           └──────────────┬───────────┘
                          │
           ┌──────────────▼──────────────┐
           │  CHATBOT ENGINE             │
           │  (src/chatbot/chatbot.py)   │
           └──────────────┬──────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    ┌────────┐      ┌──────────┐      ┌────────────┐
    │Retriever│      │Embeddings│      │Conversation│
    │         │      │Manager   │      │History     │
    └────┬────┘      └────┬─────┘      └────────────┘
         │                │
         │      ┌─────────▼─────────┐
         │      │ Sentence Transform │
         │      │ (all-MiniLM-L6-v2)│
         │      └───────────────────┘
         │
         ▼
    ┌──────────────────────────────┐
    │   DATA & MODELS              │
    │  ┌────────────────────────┐  │
    │  │ Processed Products DB  │  │
    │  │ (pandas DataFrame)     │  │
    │  └────────────────────────┘  │
    │  ┌────────────────────────┐  │
    │  │ Product Embeddings     │  │
    │  │ (numpy arrays)         │  │
    │  └────────────────────────┘  │
    └──────────────────────────────┘
         │
         ▼
    ┌──────────────────────┐
    │   DATA PIPELINE      │
    │ ┌────────────────┐   │
    │ │ Load (CSV)     │   │
    │ └────────┬───────┘   │
    │ ┌────────▼────────┐  │
    │ │ Preprocess Data │  │
    │ └────────┬────────┘  │
    │ ┌────────▼───────────┐
    │ │ Create Embeddings  │
    │ └────────────────────┘
    └──────────────────────┘
         │
         ▼
    ┌──────────────────┐
    │  DATA SOURCES    │
    │  ┌────────────┐  │
    │  │ CSV File   │  │
    │  │ 20 Products│  │
    │  └────────────┘  │
    └──────────────────┘

DATA FLOW
=========

1. INPUT LAYER (User Query)
   └─> User enters question via CLI or API

2. PROCESSING LAYER
   ├─> Query Encoding: Convert text to embeddings
   ├─> Similarity Search: Compare with product embeddings
   └─> Ranking: Sort by relevance score

3. RETRIEVAL LAYER
   ├─> Product Retriever finds top-K matching products
   ├─> Filters by similarity threshold
   └─> Returns product details and scores

4. RESPONSE GENERATION LAYER
   ├─> Format retrieved products
   ├─> Create natural language response
   └─> Add to conversation history

5. OUTPUT LAYER
   └─> Return JSON response (API) or Display (CLI)

COMPONENT DETAILS
=================

1. DATA LOADER (src/data/loader.py)
   ├─ Input: CSV file path
   ├─ Process: Read and parse CSV
   ├─ Output: Pandas DataFrame
   └─ Methods: load(), get_data(), search_products()

2. DATA PREPROCESSOR (src/data/preprocessor.py)
   ├─ Input: Raw DataFrame
   ├─ Process:
   │  ├─ Clean text (remove extra spaces)
   │  ├─ Remove duplicates
   │  ├─ Handle missing values
   │  ├─ Normalize prices
   │  └─ Create combined text features
   └─ Output: Cleaned DataFrame

3. EMBEDDINGS MANAGER (src/chatbot/embeddings.py)
   ├─ Model: sentence-transformers (all-MiniLM-L6-v2)
   ├─ Input: List of text strings
   ├─ Process: Convert text to vectors (384-dimensional)
   ├─ Output: NumPy array of embeddings
   ├─ Features: Save/load embeddings, single text encoding
   └─ Technology: PyTorch-based transformers

4. RETRIEVER (src/chatbot/retriever.py)
   ├─ Input: Query embeddings, product embeddings
   ├─ Process: Calculate cosine similarity
   ├─ Output: Top-K products with scores
   ├─ Methods:
   │  ├─ retrieve() - semantic search
   │  ├─ retrieve_by_category() - category filter
   │  ├─ retrieve_by_price_range() - price filter
   │  └─ retrieve_by_application() - application filter
   └─ Technology: scikit-learn cosine similarity

5. CHATBOT ENGINE (src/chatbot/chatbot.py)
   ├─ Input: User message
   ├─ Process:
   │  ├─ Retrieve relevant products
   │  ├─ Format product information
   │  ├─ Generate response
   │  └─ Store in history
   ├─ Output: Response with products
   └─ Features: History management, statistics

6. FLASK API (src/api/app.py)
   ├─ Framework: Flask 3.0
   ├─ Endpoints:
   │  ├─ POST /chat - send message
   │  ├─ GET /history - conversation history
   │  ├─ POST /clear-history - clear history
   │  ├─ GET /stats - statistics
   │  ├─ GET /products - list products
   │  └─ GET /products/<id> - specific product
   ├─ CORS: Enabled for all origins
   └─ Features: Auto-initialization, error handling

TECHNOLOGY STACK
================

Core:
- Python 3.8+: Programming language
- pandas 2.1.0: Data manipulation
- NumPy 1.24.0: Numerical computing

Machine Learning:
- sentence-transformers 2.2.2: Semantic embeddings
- scikit-learn 1.3.0: Similarity metrics
- PyTorch 2.0.0: Deep learning backend

Web Framework:
- Flask 3.0.0: REST API
- flask-cors 4.0.0: Cross-origin support
- python-dotenv 1.0.0: Environment configuration

NLP:
- NLTK 3.8.1: Natural language processing

EMBEDDING MODEL DETAILS
========================

Model: all-MiniLM-L6-v2
├─ Architecture: DistilBERT
├─ Size: ~22MB
├─ Embedding Dimension: 384
├─ Max Sequence Length: 256 tokens
├─ Performance: Fast (~10ms per text)
└─ Use Case: General-purpose semantic similarity

Alternatives (if needed):
├─ sentence-transformers/all-mpnet-base-v2 (768-dim, slower)
├─ all-distilroberta-v1 (768-dim)
└─ distiluse-base-multilingual-cased-v1 (512-dim, multi-lang)

SIMILARITY SEARCH ALGORITHM
===========================

1. Encode Query
   └─> sentence_transformer.encode(query)

2. Calculate Similarity
   └─> cosine_similarity(query_embedding, product_embeddings)
       Formula: cos(θ) = (A·B) / (|A||B|)
       Range: -1 to 1 (typically 0 to 1 for normalized embeddings)

3. Rank Results
   └─> Sort by similarity score (highest first)

4. Filter
   └─> Keep only scores >= SIMILARITY_THRESHOLD (default: 0.3)

5. Return Top-K
   └─> Select top K results (default: K=3)

CONVERSATION MANAGEMENT
=======================

History Structure:
├─ User Messages
│  ├─ Role: "user"
│  ├─ Content: User's question
│  └─ Timestamp: ISO format
└─ Bot Responses
   ├─ Role: "assistant"
   ├─ Content: Generated response
   └─ Timestamp: ISO format

Memory Management:
├─ Max messages in memory: 10 (configurable)
├─ FIFO eviction: Oldest messages removed first
└─ Searchable: Full history accessible via API

PERFORMANCE CHARACTERISTICS
============================

Initialization:
├─ Model Download: ~80MB (first time)
├─ Data Loading: <1 second
├─ Preprocessing: <1 second
├─ Embedding Creation: ~5-10 seconds for 20 products
└─ Total: ~10-15 seconds first run

Per Query:
├─ Encoding Query: ~10ms
├─ Similarity Search: <5ms
├─ Response Generation: <50ms
└─ Total: ~50-100ms

Memory Usage:
├─ Model: ~80MB
├─ Embeddings (20 products): ~150KB
├─ Data: ~100KB
└─ Total: ~80MB+

SCALABILITY CONSIDERATIONS
===========================

Current Capacity: 20 products
Estimated Scales:
├─ 100 products: Still <1 second queries
├─ 1000 products: ~1-2 seconds (embedding search)
├─ 10000+ products: Consider vector indexing (FAISS, Annoy)

Optimization Strategies:
├─ Use Vector Indices: FAISS, Annoy
├─ Batch Embeddings: Faster processing
├─ Caching: Pre-compute common queries
├─ Model Quantization: Reduce model size
└─ Distributed Processing: Multiple workers

ERROR HANDLING
===============

Data Loading Errors:
├─ FileNotFoundError: Gracefully handled, logs warning
├─ CSV Parse Error: Logs error, returns None
└─ Missing Columns: Processed with available data

Embedding Errors:
├─ Model Download Failed: Logs error, exception raised
├─ Out of Memory: Suggests smaller model
└─ Invalid Text: Handled with empty string fallback

API Errors:
├─ 404: Endpoint not found
├─ 400: Bad request (missing message)
├─ 500: Internal server error (logged)
└─ CORS: Enabled for all origins

DEPLOYMENT CONSIDERATIONS
===========================

Development:
├─ Flask debug mode: Enabled
├─ CORS: Allow all origins
└─ Hot reload: Supported

Production:
├─ Use WSGI server: Gunicorn, uWSGI
├─ Restrict CORS: Specific domains
├─ Enable HTTPS: SSL/TLS
├─ Load Balancing: Multiple workers
├─ Caching: Redis for embeddings
└─ Monitoring: Logging, metrics collection

SECURITY CONSIDERATIONS
=======================

Input Validation:
├─ Message length limits
├─ SQL injection: N/A (no database)
└─ XSS: API returns JSON (safe)

Model Security:
├─ Model integrity: Verify checksums
├─ Update mechanism: Regular updates
└─ Version control: Track model changes

API Security:
├─ Rate limiting: Recommended
├─ Authentication: None by default
├─ HTTPS: Recommended for production
└─ CORS: Configure for specific domains

TESTING STRATEGY
================

Unit Tests:
├─ DataLoader: test_load_data(), test_search_products()
├─ DataPreprocessor: test_preprocess_all(), test_clean_text()
└─ Location: tests/test_chatbot.py

Integration Tests:
├─ End-to-end chat flow
├─ API endpoint responses
└─ Error handling

Performance Tests:
├─ Query response time
├─ Memory usage
└─ Throughput under load

FUTURE IMPROVEMENTS
====================

Short Term:
├─ [ ] Add user authentication
├─ [ ] Implement rate limiting
├─ [ ] Cache embeddings
└─ [ ] Add logging levels

Medium Term:
├─ [ ] Fine-tune embeddings on domain data
├─ [ ] Add multi-language support
├─ [ ] Implement vector indexing (FAISS)
└─ [ ] Add database persistence

Long Term:
├─ [ ] Build web UI (React/Vue)
├─ [ ] Add advanced NLP (NER, sentiment)
├─ [ ] Implement knowledge graphs
├─ [ ] Deploy to cloud platforms
└─ [ ] Real-time collaboration features
"""
