import os
import sys
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.config import config
from src.utils.mongo import get_database
from src.chatbot.chatbot import AluminiumChatBot
from src.chatbot.embeddings import EmbeddingsManager
from src.chatbot.retriever import Retriever
import pandas as pd
import logging

logging.basicConfig(level=logging.DEBUG)

def test_doc_context():
    print("Initializing test...")
    db = get_database(config.MONGO_URI, config.MONGO_DB)
    df = pd.DataFrame([{'product_name': 'test', 'category': 'test', 'description': 'test', 'combined_text': 'test'}])
    embeddings_manager = EmbeddingsManager()
    embeddings_manager.create_embeddings(['test'])
    retriever = Retriever(embeddings_manager, df)
    
    bot = AluminiumChatBot(retriever, embeddings_manager, config, database=db, attachments_collection_name=config.MONGO_ATTACHMENTS_COLLECTION)
    
    session_id = 'chat_mmrko4r5_pzrpdx2y'
    
    try:
        attachments = bot.get_attachments_for_session = lambda *args: list(db[config.MONGO_ATTACHMENTS_COLLECTION].find({'session_id': session_id}))
        bot.database = db
        context = bot._get_document_context_for_session(session_id, 'summerize')
        print(f"Context length: {len(context)}")
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    test_doc_context()
