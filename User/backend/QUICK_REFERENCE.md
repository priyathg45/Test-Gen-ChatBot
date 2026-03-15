"""
QUICK REFERENCE - Aluminum Products Chatbot
============================================

PROJECT STRUCTURE SUMMARY
========================

src/
├── main.py                    - Interactive CLI chatbot interface
├── config.py                  - Configuration and environment settings
├── data/
│   ├── loader.py              - Load CSV data into memory
│   └── preprocessor.py        - Clean and prepare data
├── chatbot/
│   ├── embeddings.py          - Semantic embeddings using sentence-transformers
│   ├── retriever.py           - Find relevant products using similarity search
│   └── chatbot.py             - Main chatbot logic and conversation management
├── api/
│   └── app.py                 - Flask REST API server
└── utils/
    └── logger.py              - Logging setup

GETTING STARTED
===============

1. Install Dependencies:
   pip install -r requirements.txt

2. Run Interactive Chatbot:
   python -m src.main

3. Run API Server:
   python src/api/app.py
   (Access at http://localhost:5000)

KEY COMPONENTS
==============

1. DataLoader (src/data/loader.py)
   - Loads products from CSV
   - Methods: load(), get_product_by_id(), search_products(), get_stats()

2. DataPreprocessor (src/data/preprocessor.py)
   - Cleans text, removes duplicates
   - Handles missing values
   - Normalizes prices
   - Method chaining: preprocessor.preprocess_all()

3. EmbeddingsManager (src/chatbot/embeddings.py)
   - Creates vector embeddings using sentence-transformers
   - Uses model: all-MiniLM-L6-v2
   - Methods: create_embeddings(), encode_text(), save/load_embeddings()

4. Retriever (src/chatbot/retriever.py)
   - Performs semantic similarity search
   - Methods: retrieve(), retrieve_by_category(), retrieve_by_price_range()

5. AluminiumChatBot (src/chatbot/chatbot.py)
   - Main chatbot interface
   - Manages conversation history
   - Methods: chat(), get_history(), clear_history()

6. Flask API (src/api/app.py)
   - REST endpoints for chatbot
   - Endpoints: /chat, /history, /products, /stats

EXAMPLE USAGE
=============

CLI Example:
-----------
from src.data.loader import DataLoader
from src.data.preprocessor import DataPreprocessor
from src.chatbot.embeddings import EmbeddingsManager
from src.chatbot.retriever import Retriever
from src.chatbot.chatbot import AluminiumChatBot

# Load and preprocess data
loader = DataLoader('data/aluminum_products.csv')
df = loader.load()
preprocessor = DataPreprocessor(df)
df = preprocessor.preprocess_all().get_processed_data()

# Create embeddings
embeddings_mgr = EmbeddingsManager()
embeddings_mgr.create_embeddings(df['combined_text'].tolist())

# Initialize retriever and chatbot
retriever = Retriever(embeddings_mgr, df)
chatbot = AluminiumChatBot(retriever, embeddings_mgr, config)

# Chat
response = chatbot.chat("Tell me about 6061 aluminum alloy")
print(response['message'])

API Example:
-----------
curl -X POST http://localhost:5000/chat \\
  -H "Content-Type: application/json" \\
  -d '{"message": "What aluminum alloys are used in aerospace?"}'

CONFIGURATION
==============

Environment Variables (.env):
- FLASK_ENV: development/production
- FLASK_DEBUG: True/False
- DATA_PATH: Path to CSV file
- MODEL_NAME: Sentence transformer model
- TOP_K_RESULTS: Number of products to return
- SIMILARITY_THRESHOLD: Minimum similarity score (0-1)

DEFAULT VALUES
==============

Model: all-MiniLM-L6-v2 (384-dimensional embeddings)
Top K Results: 3
Similarity Threshold: 0.3
Max Chat History: 10 messages
Temperature: 0.7

DATASET INFORMATION
====================

Columns in aluminum_products.csv:
- product_id: Unique identifier (1-20)
- product_name: Product name
- category: Category (Aerospace, Marine, Aviation, etc.)
- description: Product description
- price: Price in USD
- specifications: Technical specifications
- applications: Typical uses
- manufacturer: Manufacturer name
- stock_level: Available quantity

Total Products: 20
Categories: 7 (Aerospace, Marine, Aviation, Construction, etc.)
Price Range: $95 - $950

TESTING
========

Run unit tests:
python -m unittest discover -s tests -p "test_*.py"

Test modules:
- tests/test_chatbot.py: Tests for DataLoader and DataPreprocessor

TROUBLESHOOTING
================

Model Download Fails:
  python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

Port 5000 Already in Use:
  export FLASK_RUN_PORT=5001
  python -m flask run

Memory Issues:
  Change MODEL_NAME to a smaller model in .env

PERFORMANCE TIPS
==================

- First run downloads model (~80MB) - be patient
- Embeddings for 20 products: ~5-10 seconds
- Query response time: <1 second (after initialization)
- Use similarity_threshold to filter weak matches

ADVANCED USAGE
===============

Customize Configuration:
  from src.config import Config
  Config.TOP_K_RESULTS = 5
  Config.SIMILARITY_THRESHOLD = 0.5

Save/Load Embeddings:
  embeddings_mgr.save_embeddings('models/embeddings.pkl')
  embeddings_mgr.load_embeddings('models/embeddings.pkl')

Access Conversation History:
  history = chatbot.get_history()
  for msg in history:
      print(f"{msg['role']}: {msg['content']}")

Get Statistics:
  stats = chatbot.get_stats()
  print(f"Total messages: {stats['total_messages']}")

USEFUL COMMANDS
================

List all products:
  curl http://localhost:5000/products

Get products by category:
  curl "http://localhost:5000/products?category=aerospace"

Get specific product:
  curl http://localhost:5000/products/1

Get conversation history:
  curl http://localhost:5000/history

Clear history:
  curl -X POST http://localhost:5000/clear-history

Check health:
  curl http://localhost:5000/health

Get statistics:
  curl http://localhost:5000/stats
"""
