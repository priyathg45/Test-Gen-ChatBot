"""Data loader module for reading products from CSV or MongoDB."""
import pandas as pd
import logging
from typing import Optional

from src.utils.mongo import get_collection

logger = logging.getLogger(__name__)

class DataLoader:
    """Load and manage aluminum products data from CSV files."""
    
    def __init__(
        self,
        filepath: str,
        use_mongo: bool = False,
        mongo_uri: Optional[str] = None,
        mongo_db: Optional[str] = None,
        mongo_collection: str = "products",
    ):
        """Initialize the DataLoader."""
        self.filepath = filepath
        self.use_mongo = use_mongo and bool(mongo_uri)
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection
        self.df: Optional[pd.DataFrame] = None
        
    def load(self) -> Optional[pd.DataFrame]:
        """Load data from MongoDB (if enabled) or CSV."""
        if self.use_mongo:
            return self._load_from_mongo()
        return self._load_from_csv()

    def _load_from_csv(self) -> Optional[pd.DataFrame]:
        try:
            self.df = pd.read_csv(self.filepath)
            logger.info(f"Successfully loaded {len(self.df)} products from {self.filepath}")
            return self.df
        except FileNotFoundError:
            logger.error(f"File not found: {self.filepath}")
            return None
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return None

    def _load_from_mongo(self) -> Optional[pd.DataFrame]:
        try:
            collection = get_collection(self.mongo_uri, self.mongo_db, self.mongo_collection)
            docs = list(collection.find({}))
            if not docs:
                logger.warning("MongoDB collection is empty; no products loaded")
                return None

            df = pd.DataFrame(docs)

            # Drop MongoDB internal id and normalize types where possible
            if "_id" in df.columns:
                df = df.drop(columns=["_id"])

            if "product_id" in df.columns:
                try:
                    df["product_id"] = pd.to_numeric(df["product_id"])
                except Exception:
                    pass

            self.df = df
            logger.info(
                "Successfully loaded %s products from MongoDB collection %s",
                len(df),
                self.mongo_collection,
            )
            return self.df
        except Exception as e:
            logger.error(f"Error loading data from MongoDB: {str(e)}")
            return None
    
    def get_data(self) -> Optional[pd.DataFrame]:
        """
        Get the loaded data.
        
        Returns:
            Optional[DataFrame]: The loaded DataFrame
        """
        if self.df is None:
            return self.load()
        return self.df
    
    def get_product_by_id(self, product_id: int) -> Optional[dict]:
        """
        Retrieve a specific product by ID.
        
        Args:
            product_id (int): The product ID
            
        Returns:
            Optional[dict]: Product data as dictionary or None
        """
        if self.df is None:
            self.load()
            
        if self.df is None:
            return None
        
        product = self.df[self.df['product_id'] == product_id]
        if not product.empty:
            return product.iloc[0].to_dict()
        return None
    
    def search_products(self, keyword: str) -> pd.DataFrame:
        """
        Search products by keyword in product name and category.
        
        Args:
            keyword (str): Search keyword
            
        Returns:
            DataFrame: Filtered products
        """
        if self.df is None:
            self.load()
            
        if self.df is None:
            return pd.DataFrame()
        
        keyword_lower = keyword.lower()
        
        # In this dataset, actual product info is in specifications/product_summary
        mask = (
            (self.df['product_name'].str.lower().str.contains(keyword_lower, na=False)) |
            (self.df['category'].str.lower().str.contains(keyword_lower, na=False)) |
            (self.df['specifications'].str.lower().str.contains(keyword_lower, na=False)) |
            (self.df['product_summary'].str.lower().str.contains(keyword_lower, na=False))
        )
        return self.df[mask]
    
    def get_stats(self) -> dict:
        """
        Get basic statistics about the dataset.
        
        Returns:
            dict: Statistics including total products, categories, price range
        """
        if self.df is None:
            self.load()
            
        if self.df is None:
            return {
                'total_products': 0,
                'categories': [],
                'avg_price': 0.0,
                'min_price': 0.0,
                'max_price': 0.0
            }
        
        return {
            'total_products': len(self.df),
            'categories': self.df['category'].unique().tolist(),
            'avg_price': self.df['price'].mean(),
            'min_price': self.df['price'].min(),
            'max_price': self.df['price'].max()
        }
