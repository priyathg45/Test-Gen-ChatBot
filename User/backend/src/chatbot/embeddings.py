"""Embeddings module for creating vector representations of text."""
import logging
import numpy as np
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
import pickle
import os

logger = logging.getLogger(__name__)

class EmbeddingsManager:
    """Create and manage embeddings for products using sentence transformers."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the EmbeddingsManager.
        
        Args:
            model_name (str): Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = None
        self.embeddings = None
        self.texts = None
        logger.info(f"Loading model: {model_name}")
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model."""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Successfully loaded model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for a list of texts.
        
        Args:
            texts (List[str]): List of texts to embed
            
        Returns:
            np.ndarray: Array of embeddings
        """
        try:
            self.texts = texts
            self.embeddings = self.model.encode(texts, show_progress_bar=True)
            logger.info(f"Created embeddings for {len(texts)} texts")
            return self.embeddings
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            return None
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode a single text to embedding.
        
        Args:
            text (str): Text to encode
            
        Returns:
            np.ndarray: Embedding vector
        """
        try:
            return self.model.encode(text)
        except Exception as e:
            logger.error(f"Error encoding text: {str(e)}")
            return None
    
    def save_embeddings(self, filepath: str):
        """
        Save embeddings to file.
        
        Args:
            filepath (str): Path to save embeddings
        """
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                pickle.dump({
                    'embeddings': self.embeddings,
                    'texts': self.texts,
                    'model_name': self.model_name
                }, f)
            logger.info(f"Saved embeddings to {filepath}")
        except Exception as e:
            logger.error(f"Error saving embeddings: {str(e)}")
    
    def load_embeddings(self, filepath: str) -> bool:
        """
        Load embeddings from file.
        
        Args:
            filepath (str): Path to load embeddings from
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.embeddings = data['embeddings']
                self.texts = data['texts']
                logger.info(f"Loaded embeddings from {filepath}")
                return True
        except FileNotFoundError:
            logger.warning(f"Embeddings file not found: {filepath}")
            return False
        except Exception as e:
            logger.error(f"Error loading embeddings: {str(e)}")
            return False
    
    def get_embeddings(self) -> np.ndarray:
        """
        Get the embeddings.
        
        Returns:
            np.ndarray: Embeddings array
        """
        return self.embeddings
    
    def get_texts(self) -> List[str]:
        """
        Get the texts used for embeddings.
        
        Returns:
            List[str]: List of texts
        """
        return self.texts
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings.
        
        Returns:
            int: Embedding dimension
        """
        if self.embeddings is not None and len(self.embeddings) > 0:
            return self.embeddings[0].shape[0]
        return 0
