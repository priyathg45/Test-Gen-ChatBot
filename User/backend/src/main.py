"""Main entry point for the chatbot application."""
import logging
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import setup_logging
from src.config import Config
from src.data.loader import DataLoader
from src.data.preprocessor import DataPreprocessor
from src.chatbot.embeddings import EmbeddingsManager
from src.chatbot.retriever import Retriever
from src.chatbot.chatbot import AluminiumChatBot
from src.utils.mongo import get_collection, ensure_history_collection

# Setup logging
logger = setup_logging()

def initialize_chatbot():
    """Initialize and return the chatbot."""
    try:
        logger.info("=" * 50)
        logger.info("Initializing Aluminum Products Chatbot")
        logger.info("=" * 50)
        
        history_collection = None
        mongo_products_collection = None

        if Config.USE_MONGO and Config.MONGO_URI:
            try:
                mongo_products_collection = get_collection(
                    Config.MONGO_URI,
                    Config.MONGO_DB,
                    Config.MONGO_PRODUCTS_COLLECTION,
                    **Config.MONGO_CLIENT_KWARGS,
                )
                history_collection = ensure_history_collection(
                    Config.MONGO_URI,
                    Config.MONGO_DB,
                    Config.MONGO_HISTORY_COLLECTION,
                    **Config.MONGO_CLIENT_KWARGS,
                )
                mongo_products_collection.database.client.admin.command("ping")
                logger.info(
                    "MongoDB connected: %s/%s (products) | %s (history)",
                    Config.MONGO_URI,
                    Config.MONGO_DB,
                    Config.MONGO_HISTORY_COLLECTION,
                )
            except Exception as mongo_exc:
                mongo_products_collection = None
                history_collection = None
                logger.error(f"MongoDB connection failed; continuing with CSV/in-memory: {mongo_exc}")

        # Load data (prefer preprocessed CSV when available for more accurate embeddings)
        from pathlib import Path
        data_path = Config.DATA_PATH
        loaded_from_preprocessed = False
        if not Config.USE_MONGO or not mongo_products_collection:
            if getattr(Config, 'PREFER_PREPROCESSED_CSV', True):
                base = Path(Config.DATA_PATH)
                preprocessed_path = base.parent / "aluminum_products_preprocessed.csv"
                if preprocessed_path.exists():
                    data_path = str(preprocessed_path)
                    loaded_from_preprocessed = True
                    logger.info("Using preprocessed dataset: %s", preprocessed_path)
        logger.info("Loading data...")
        data_loader = DataLoader(
            data_path,
            use_mongo=Config.USE_MONGO and bool(mongo_products_collection),
            mongo_uri=Config.MONGO_URI,
            mongo_db=Config.MONGO_DB,
            mongo_collection=Config.MONGO_PRODUCTS_COLLECTION,
        )
        df = data_loader.load()

        if df is None and Config.USE_MONGO:
            logger.warning("MongoDB products not available; retrying with CSV at %s", Config.DATA_PATH)
            data_loader = DataLoader(Config.DATA_PATH, use_mongo=False)
            df = data_loader.load()
        
        if df is None:
            logger.error("Startup aborted: no product data available after Mongo/CSV attempts")
            raise Exception("Failed to load data from MongoDB and CSV")
        
        if not loaded_from_preprocessed:
            logger.info("Preprocessing data...")
            preprocessor = DataPreprocessor(df)
            df = preprocessor.preprocess_all().get_processed_data()
        elif 'combined_text' not in df.columns:
            preprocessor = DataPreprocessor(df)
            df = preprocessor.add_text_features().get_processed_data()
        logger.info(f"Data ready: {len(df)} products")
        
        # Create embeddings
        logger.info(f"Creating embeddings using {Config.MODEL_NAME}...")
        embeddings_manager = EmbeddingsManager(model_name=Config.MODEL_NAME)
        
        # Prepare texts for embedding
        if 'combined_text' in df.columns:
            texts = df['combined_text'].tolist()
        else:
            texts = (df['product_name'] + ' ' + df['category'] + ' ' + df['description']).tolist()
        
        embeddings_manager.create_embeddings(texts)
        logger.info(f"Embeddings created: {len(texts)} product embeddings")
        
        # Initialize retriever
        logger.info("Initializing retriever...")
        retriever = Retriever(
            embeddings_manager,
            df,
            top_k=Config.TOP_K_RESULTS,
            similarity_threshold=Config.SIMILARITY_THRESHOLD
        )
        
        # Initialize chatbot
        logger.info("Initializing chatbot...")
        chatbot_instance = AluminiumChatBot(
            retriever,
            embeddings_manager,
            Config,
            history_collection=history_collection,
        )

        if history_collection is not None:
            logger.info("Chat history persistence: MongoDB (%s)", Config.MONGO_HISTORY_COLLECTION)
        else:
            logger.warning("Chat history persistence: in-memory (Mongo disabled or unreachable)")
        
        logger.info("=" * 50)
        logger.info("Chatbot initialized successfully!")
        logger.info("=" * 50)
        
        return chatbot_instance
    
    except Exception as e:
        logger.error(f"Error initializing chatbot: {str(e)}")
        raise

def main():
    """Main function for interactive chatbot."""
    try:
        chatbot_instance = initialize_chatbot()
        
        print("\n" + "=" * 50)
        print("ALUMINUM PRODUCTS CHATBOT")
        print("=" * 50)
        print("\nWelcome! Ask me anything about aluminum products.")
        print("Type 'exit' to quit, 'history' to see conversation, 'stats' for statistics.\n")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'exit':
                    print("\nThank you for using the Aluminum Products Chatbot!")
                    break
                
                if user_input.lower() == 'history':
                    history = chatbot_instance.get_history()
                    print("\n--- CONVERSATION HISTORY ---")
                    for msg in history:
                        role = "You" if msg['role'] == 'user' else "Bot"
                        print(f"\n{role}: {msg['content'][:100]}...")
                    continue
                
                if user_input.lower() == 'stats':
                    stats = chatbot_instance.get_stats()
                    print("\n--- CHATBOT STATISTICS ---")
                    for key, value in stats.items():
                        print(f"{key}: {value}")
                    continue
                
                # Get response from chatbot
                response = chatbot_instance.chat(user_input)
                
                print("\nBot:")
                print(response['message'])
                
                if response['products_count'] > 0:
                    print(f"\n(Found {response['products_count']} relevant products)")
            
            except KeyboardInterrupt:
                print("\n\nThank you for using the Aluminum Products Chatbot!")
                break
            except Exception as e:
                logger.error(f"Error in chat loop: {str(e)}")
                print(f"\nError: {str(e)}")
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
