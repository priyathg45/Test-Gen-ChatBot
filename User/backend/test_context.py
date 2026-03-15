import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.config import config
from src.utils.mongo import get_database
from src.chatbot.chatbot import AluminiumChatBot
from src.chatbot.embeddings import EmbeddingsManager
from src.chatbot.retriever import Retriever
import pandas as pd

def test_doc_context():
    print("Initializing test...")
    db = get_database(config.MONGO_URI, config.MONGO_DB)
    
    # Minimal mock objects
    df = pd.DataFrame([{'product_name': 'test', 'category': 'test', 'description': 'test', 'combined_text': 'test'}])
    embeddings_manager = EmbeddingsManager()
    embeddings_manager.create_embeddings(['test'])
    retriever = Retriever(embeddings_manager, df)
    
    bot = AluminiumChatBot(
        retriever=retriever,
        embeddings_manager=embeddings_manager,
        config=config,
        database=db,
        attachments_collection_name=config.MONGO_ATTACHMENTS_COLLECTION
    )
    
    session_id = 'chat_mmrko4r5_pzrpdx2y' # This is the user's latest session ID from the DB
    query = 'summerize given pdf'
    
    print(f"Calling _get_document_context_for_session for '{session_id}'...")
    try:
        context = bot._get_document_context_for_session(session_id, query)
        print(f"Context length: {len(context)}")
        print(f"Context snippet: {context[:500] if context else 'EMPTY STRING!'}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_doc_context()
