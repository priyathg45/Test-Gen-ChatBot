"""Embeddings module for creating vector representations of text."""
import logging
import numpy as np
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
import pickle
import os
import json
import urllib.request

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
        
        try:
            from src.config import config
            self.use_ollama = getattr(config, "USE_OLLAMA_FOR_EMBEDDINGS", False)
            self.ollama_base_url = getattr(config, "OLLAMA_BASE_URL", "http://localhost:11434")
        except ImportError:
            self.use_ollama = False
            self.ollama_base_url = "http://localhost:11434"

        logger.info(f"Embeddings manager initializing with model: {model_name} (Ollama={self.use_ollama})")
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model if not using Ollama."""
        if self.use_ollama:
            logger.info("Skipping local PyTorch model load; routing embeddings to Ollama API.")
            return

        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Successfully loaded sentence-transformer model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for a list of texts.
        """
        try:
            self.texts = texts
            if self.use_ollama:
                # Process sequentially for Ollama embeddings
                embeddings = []
                failed = False
                for idx, text in enumerate(texts):
                    emb = self._get_ollama_embedding(text)
                    if emb is None:
                        logger.error(f"Failed to create Ollama embedding for text index {idx}. Falling back to SentenceTransformers.")
                        failed = True
                        break
                    embeddings.append(emb)
                
                if not failed and embeddings:
                    self.embeddings = np.array(embeddings, dtype=np.float32)
                else:
                    logger.warning(f"Ollama failed for {self.model_name}. Loading SentenceTransformer fallback.")
                    if self.model is None:
                        self.model = SentenceTransformer(self.model_name)
                    self.embeddings = self.model.encode(texts, show_progress_bar=True)
            else:
                self.embeddings = self.model.encode(texts, show_progress_bar=True)
            
            logger.info(f"Created embeddings for {len(texts)} texts using {self.model_name}")
            return self.embeddings
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            return None
    
    def encode_text(self, text: str) -> np.ndarray:
        """
        Encode a single text to embedding.
        """
        try:
            if self.use_ollama:
                emb = self._get_ollama_embedding(text)
                if emb is not None:
                    return np.array(emb, dtype=np.float32)
                logger.warning(f"Ollama embedding failed for text. Falling back to SentenceTransformer.")
                if self.model is None:
                     self.model = SentenceTransformer(self.model_name)
            
            return self.model.encode(text)
        except Exception as e:
            logger.error(f"Error encoding text: {str(e)}")
            return None
            
    def _get_ollama_embedding(self, text: str) -> List[float]:
        """Call Ollama /api/embeddings endpoint for a single text."""
        try:
            body = {
                "model": self.model_name,
                "prompt": text
            }
            req = urllib.request.Request(
                f"{self.ollama_base_url.rstrip('/')}/api/embeddings",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("embedding")
        except urllib.error.HTTPError as he:
            if he.code == 404:
                logger.error(f"Ollama API 404: Check if model '{self.model_name}' is installed (e.g. 'ollama pull {self.model_name}').")
            else:
                logger.error(f"Ollama HTTP error {he.code}: {he.read().decode('utf-8')}")
            return None
        except Exception as e:
            logger.error(f"Ollama API embedding failed: {e}")
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
