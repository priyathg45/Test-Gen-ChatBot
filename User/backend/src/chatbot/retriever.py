"""Retrieval module for finding relevant products based on queries."""
import numpy as np
import logging
from typing import List, Tuple, Dict, Optional
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

logger = logging.getLogger(__name__)

class Retriever:
    """Retrieve relevant products based on semantic similarity."""
    
    def __init__(self, embeddings_manager, dataframe: pd.DataFrame, top_k: int = 3, 
                 similarity_threshold: float = 0.3):
        """
        Initialize the Retriever.
        
        Args:
            embeddings_manager: EmbeddingsManager instance
            dataframe (pd.DataFrame): Product data
            top_k (int): Number of top results to return
            similarity_threshold (float): Minimum similarity score
        """
        self.embeddings_manager = embeddings_manager
        self.dataframe = dataframe
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
    
    def retrieve(self, query: str) -> List[Dict]:
        """
        Retrieve relevant products for a query.
        
        Args:
            query (str): User query
            
        Returns:
            List[Dict]: List of relevant products with scores
        """
        try:
            # Encode the query
            query_embedding = self.embeddings_manager.encode_text(query)
            
            if query_embedding is None:
                logger.error("Failed to encode query")
                return []
            
            # Get all product embeddings
            product_embeddings = self.embeddings_manager.get_embeddings()
            
            if product_embeddings is None or len(product_embeddings) == 0:
                logger.error("No product embeddings available")
                return []
            
            # Calculate similarity scores
            similarities = cosine_similarity([query_embedding], product_embeddings)[0]
            
            # Get top K indices
            top_indices = np.argsort(similarities)[::-1][:self.top_k]
            
            # Filter by similarity threshold and prepare results
            results = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score >= self.similarity_threshold:
                    product = self.dataframe.iloc[idx].to_dict()
                    product['similarity_score'] = score
                    results.append(product)

            # If nothing passed the threshold, still return the best matches to avoid empty answers
            if not results:
                for idx in top_indices:
                    product = self.dataframe.iloc[idx].to_dict()
                    product['similarity_score'] = float(similarities[idx])
                    results.append(product)

            logger.info(f"Retrieved {len(results)} products for query: '{query}'")
            return results
        
        except Exception as e:
            logger.error(f"Error retrieving products: {str(e)}")
            return []

    def retrieve_by_keywords(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """
        Retrieve products by simple keyword matching across text fields.

        Args:
            query (str): User query
            top_k (Optional[int]): Limit number of results

        Returns:
            List[Dict]: Matched products
        """
        try:
            tokens = [t for t in query.lower().split() if len(t) > 2]
            if not tokens:
                return []

            text_fields = ["product_name", "category", "description", "specifications", "applications", "manufacturer"]
            if "job_id" in self.dataframe.columns:
                text_fields.extend(["job_id", "job_name", "product_summary", "customer_company"])
            scores = []
            for idx, row in self.dataframe.iterrows():
                haystack = " ".join(str(row.get(col, "")).lower() for col in text_fields)
                match_count = sum(1 for t in tokens if t in haystack)
                if match_count:
                    scores.append((idx, match_count))

            if not scores:
                return []

            scores.sort(key=lambda item: item[1], reverse=True)
            limit = top_k or self.top_k
            results = []
            for idx, match_count in scores[:limit]:
                product = self.dataframe.iloc[idx].to_dict()
                product['keyword_match_count'] = match_count
                results.append(product)

            logger.info(f"Retrieved {len(results)} products by keyword match for query: '{query}'")
            return results
        except Exception as e:
            logger.error(f"Error retrieving products by keywords: {str(e)}")
            return []
    
    def retrieve_by_category(self, category: str) -> List[Dict]:
        """
        Retrieve products by category.
        
        Args:
            category (str): Product category
            
        Returns:
            List[Dict]: List of products in the category
        """
        try:
            category_lower = category.lower()
            mask = self.dataframe['category'].str.lower().str.contains(category_lower, na=False)
            results = self.dataframe[mask].to_dict('records')
            logger.info(f"Retrieved {len(results)} products for category: '{category}'")
            return results
        except Exception as e:
            logger.error(f"Error retrieving products by category: {str(e)}")
            return []
    
    def retrieve_by_price_range(self, min_price: float, max_price: float) -> List[Dict]:
        """
        Retrieve products within a price range.
        
        Args:
            min_price (float): Minimum price
            max_price (float): Maximum price
            
        Returns:
            List[Dict]: Products within price range
        """
        try:
            mask = (self.dataframe['price'] >= min_price) & (self.dataframe['price'] <= max_price)
            results = self.dataframe[mask].to_dict('records')
            logger.info(f"Retrieved {len(results)} products in price range ${min_price}-${max_price}")
            return results
        except Exception as e:
            logger.error(f"Error retrieving products by price: {str(e)}")
            return []
    
    def retrieve_by_application(self, application: str) -> List[Dict]:
        """
        Retrieve products by application.
        
        Args:
            application (str): Application type
            
        Returns:
            List[Dict]: Products for the application
        """
        try:
            app_lower = application.lower()
            mask = self.dataframe['applications'].str.lower().str.contains(app_lower, na=False)
            results = self.dataframe[mask].to_dict('records')
            logger.info(f"Retrieved {len(results)} products for application: '{application}'")
            return results
        except Exception as e:
            logger.error(f"Error retrieving products by application: {str(e)}")
            return []
    
    def set_top_k(self, top_k: int):
        """
        Set the number of top results to return.
        
        Args:
            top_k (int): Number of results
        """
        self.top_k = top_k
    
    def set_similarity_threshold(self, threshold: float):
        """
        Set the similarity threshold.
        
        Args:
            threshold (float): Similarity threshold
        """
        self.similarity_threshold = threshold
