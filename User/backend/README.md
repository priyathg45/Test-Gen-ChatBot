# Aluminum Products Chatbot

An intelligent chatbot system for providing information about aluminum products. This chatbot uses machine learning embeddings and semantic search to answer questions about aluminum alloys, specifications, applications, and more.

## Features

- **Semantic Search**: Uses sentence transformers to find relevant products based on user queries
- **Product Database**: CSV-based dataset with 20+ aluminum products
- **Data Preprocessing**: Automatic cleaning and preparation of product data
- **RESTful API**: Flask-based API for easy integration
- **Conversation Management**: Maintains conversation history
- **Multiple Query Types**: Supports various ways to search products:
  - Semantic similarity search
  - Category-based search
  - Price range filtering
  - Application-based search

## Project Structure

```
genesis-chat-bot/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment configuration example
├── .gitignore                         # Git ignore rules
│
├── data/
│   └── aluminum_products.csv          # Product dataset
│
├── src/
│   ├── __init__.py
│   ├── main.py                        # Interactive CLI entry point
│   ├── config.py                      # Configuration management
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py                  # CSV data loader
│   │   └── preprocessor.py            # Data preprocessing
│   │
│   ├── chatbot/
│   │   ├── __init__.py
│   │   ├── embeddings.py              # Embedding management
│   │   ├── retriever.py               # Product retrieval logic
│   │   └── chatbot.py                 # Main chatbot class
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py                     # Flask API application
│   │
│   └── utils/
│       ├── __init__.py
│       └── logger.py                  # Logging utilities
│
├── models/
│   └── .gitkeep                       # Directory for saved models/embeddings
│
└── tests/
    ├── __init__.py
    └── test_chatbot.py                # Unit tests
```

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd genesis-chat-bot
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env if needed (optional - defaults work fine)
   ```

## Usage

### Option 1: Interactive CLI

Run the chatbot in interactive mode:

```bash
python -m src.main
```

Then type your questions about aluminum products:
```
You: Tell me about aerospace aluminum alloys

Bot: [Detailed response with relevant products]

You: What's the price of 6061-T6?

Bot: [Product information and specifications]
```

**Commands:**
- Type any question to chat
- `history` - View conversation history
- `stats` - View chatbot statistics
- `exit` - Exit the application

### Option 2: Flask API

Start the API server:

```bash
python -m flask run
# or
python src/api/app.py
```

The API will be available at `http://localhost:5000`

#### API Endpoints

**Home**
```
GET /
```
Returns available endpoints and API information.

**Health Check**
```
GET /health
```
Check if the chatbot is running and initialized.

**Chat**
```
POST /chat
Content-Type: application/json

{
  "message": "Tell me about aluminum alloys for aerospace"
}
```
Response:
```json
{
  "success": true,
  "message": "Detailed response with product information",
  "retrieved_products": [...],
  "products_count": 3,
  "timestamp": "2024-01-15T10:30:00"
}
```

**Get Conversation History**
```
GET /history
```
Returns all messages in the current conversation.

**Clear Conversation History**
```
POST /clear-history
```
Clears the conversation history.

**Get Statistics**
```
GET /stats
```
Returns chatbot statistics including message counts and model information.

**Get All Products**
```
GET /products
GET /products?category=aerospace
GET /products?limit=5
```
Returns list of products with optional filters.

**Get Specific Product**
```
GET /products/<product_id>
```
Returns details for a specific product.

### Example API Calls

Using `curl`:

```bash
# Chat with the bot
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the prices of marine grade aluminum?"}'

# Get all products
curl http://localhost:5000/products

# Get products in aerospace category
curl "http://localhost:5000/products?category=aerospace"

# Get conversation history
curl http://localhost:5000/history

# Get statistics
curl http://localhost:5000/stats
```

Using Python:

```python
import requests

url = "http://localhost:5000/chat"
payload = {"message": "Tell me about 7075 aluminum alloy"}
response = requests.post(url, json=payload)
print(response.json())
```

## Data Format

The chatbot uses a CSV file with the following columns:

| Column | Description |
|--------|-------------|
| product_id | Unique identifier |
| product_name | Name of the product |
| category | Product category (Aerospace, Marine, etc.) |
| description | Detailed description |
| price | Price in USD |
| specifications | Technical specifications |
| applications | Typical applications |
| manufacturer | Manufacturer name |
| stock_level | Current stock level |

### Creating a 1,000-row dataset

If you need a larger dataset for training or stress-testing, a generator is available:

```powershell
python -m src.data.generate_dataset --target-size 1000 --seed 42
```

This produces two files under `data/`:
- `aluminum_products_1000.csv`: synthetic raw data (1,000 rows)
- `aluminum_products_1000_processed.csv`: cleaned data with `combined_text` ready for embeddings

To make the chatbot use the larger dataset, set `DATA_PATH` in `.env` to the processed file path:

```
DATA_PATH=data/aluminum_products_1000_processed.csv
```

## Configuration

Edit `.env` file to customize:

```env
# Flask settings
FLASK_ENV=development
FLASK_DEBUG=True

# Data settings
DATA_PATH=data/aluminum_products.csv

# ML Model settings
MODEL_NAME=all-MiniLM-L6-v2
TOP_K_RESULTS=3                    # Number of products to return
SIMILARITY_THRESHOLD=0.3           # Minimum similarity score
```

## How It Works

1. **Data Loading**: Reads aluminum products from CSV file
2. **Preprocessing**: Cleans and prepares data for embedding
3. **Embedding**: Creates vector representations using sentence-transformers
4. **Retrieval**: Uses semantic similarity to find relevant products
5. **Response Generation**: Creates natural language responses based on retrieved products

## Testing

Run the test suite:

```bash
python -m pytest tests/
# or
python -m unittest discover -s tests -p "test_*.py"
```

## Running on CPU and PDF / document QA

- **CPU-only**: The app runs on CPU by default. In `.env`, `LOCAL_LLM_DEVICE=cpu` (or leave unset). For faster embedding/search, the default model is `all-mpnet-base-v2`; for lower memory use `MODEL_NAME=all-MiniLM-L6-v2`.
- **PDF/document answers**: By default, document QA uses **extracted text only** (no LLM), so answers return in a few seconds. Set `USE_OLLAMA_FOR_DOCUMENTS=true` only if Ollama is running (`ollama run llama3.2`). Set `LOCAL_LLM_ENABLED=true` to use the in-process model (slow on CPU; better with GPU).

## Making the model more powerful

- **Larger embedding model**: In `.env` set `MODEL_NAME=all-mpnet-base-v2` (default) for better accuracy, or a larger sentence-transformers model.
- **More/better product data**: Add or refine rows in your CSV and set `DATA_PATH` to the file. Use `src.data.generate_dataset` for larger synthetic data.
- **Ollama (recommended for document QA)**: Install [Ollama](https://ollama.com), run e.g. `ollama run llama3.2`, then set `USE_OLLAMA_FOR_DOCUMENTS=true` in `.env` for LLM-powered document answers.
- **Fine-tuning / training**: To train or fine-tune a model (e.g. on your own product docs), use external tooling (e.g. Hugging Face TRL, or Ollama with a custom model). The chatbot uses the embedding model for search and optional LLM for generation; training would involve exporting data and fine-tuning outside this repo, then pointing `MODEL_NAME` or Ollama at the new model.

## Performance Notes

- **First Run**: The first run takes longer as it downloads the embedding model (~80MB)
- **Embedding**: Creating embeddings for 20 products takes ~5-10 seconds
- **Queries**: Individual queries typically respond in <1 second
- **PDF chat**: With default settings (no Ollama, no local LLM), document answers use extracted text and return quickly. Enable Ollama or local LLM only if you need generated summaries and accept longer response times.

## Troubleshooting

### Model Download Issues
If the sentence-transformer model fails to download:
```bash
# Pre-download the model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Port Already in Use
If port 5000 is already in use:
```bash
# Change in src/api/app.py or use Flask environment variable
export FLASK_RUN_PORT=5001
python -m flask run
```

### Memory Issues
For systems with limited memory, you can use a smaller model:
```
MODEL_NAME=distiluse-base-multilingual-cased-v1
```

## Technologies Used

- **Python 3.8+**: Core language
- **pandas**: Data manipulation and analysis
- **scikit-learn**: Machine learning utilities
- **sentence-transformers**: Semantic embeddings
- **Flask**: Web framework
- **NLTK**: Natural language processing
- **PyTorch**: Deep learning backend (for transformers)

## Future Enhancements

- [ ] Multi-language support
- [ ] Fine-tuning models on domain-specific data
- [ ] Caching embeddings for faster startup
- [ ] User authentication and conversation persistence
- [ ] Advanced NLP techniques (named entity recognition, etc.)
- [ ] Integration with external databases
- [ ] Web UI interface
- [ ] Deployment to cloud platforms

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions, please create an issue in the repository or contact the development team.

## Author

Created by: Pavithra Hatharasinghe

## Version History

- **v1.0.0** (January 15, 2026): Initial release
  - Basic chatbot functionality
  - Semantic search capabilities
  - Flask API implementation
  - CSV data support