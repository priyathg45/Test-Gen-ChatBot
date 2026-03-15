"""Data preprocessing module for cleaning and preparing data."""
import pandas as pd
import logging
from typing import Optional, List
import re

logger = logging.getLogger(__name__)

class DataPreprocessor:
    """Preprocess and clean aluminum products data."""
    
    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize the DataPreprocessor.
        
        Args:
            dataframe (pd.DataFrame): The DataFrame to preprocess
        """
        self.df = dataframe.copy()
        self.original_df = dataframe.copy()
        
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing special characters and extra spaces.
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text
        """
        if not isinstance(text, str):
            return str(text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def clean_text_columns(self, columns: Optional[List[str]] = None) -> 'DataPreprocessor':
        """
        Clean text columns by removing extra spaces and special characters.
        
        Args:
            columns (Optional[List[str]]): Specific columns to clean, or all if None
            
        Returns:
            DataPreprocessor: Self for method chaining
        """
        if columns is None:
            columns = self.df.select_dtypes(include=['object']).columns.tolist()
        
        for col in columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].apply(self.clean_text)
                logger.info(f"Cleaned column: {col}")
        
        return self
    
    def remove_duplicates(self, subset: Optional[List[str]] = None) -> 'DataPreprocessor':
        """
        Remove duplicate rows.
        
        Args:
            subset (Optional[List[str]]): Columns to consider for duplicates
            
        Returns:
            DataPreprocessor: Self for method chaining
        """
        original_len = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset)
        logger.info(f"Removed {original_len - len(self.df)} duplicate rows")
        return self
    
    def handle_missing_values(self, strategy: str = 'fill') -> 'DataPreprocessor':
        """
        Handle missing values.
        
        Args:
            strategy (str): Strategy to use - 'drop' or 'fill'. Default 'fill' to keep AAW job rows.
            
        Returns:
            DataPreprocessor: Self for method chaining
        """
        if strategy == 'drop':
            original_len = len(self.df)
            self.df = self.df.dropna(subset=['product_name', 'category', 'description'] if all(c in self.df.columns for c in ['product_name', 'category', 'description']) else None)
            logger.info(f"Removed {original_len - len(self.df)} rows with missing values")
        elif strategy == 'fill':
            for col in self.df.columns:
                if self.df[col].dtype == 'object':
                    self.df[col] = self.df[col].fillna('')
                elif col == 'price' or str(self.df[col].dtype) in ('int64', 'float64'):
                    self.df[col] = self.df[col].fillna(0)
                else:
                    try:
                        self.df[col] = self.df[col].fillna(self.df[col].mean())
                    except Exception:
                        self.df[col] = self.df[col].fillna(0)
            logger.info("Filled missing values")
        
        return self
    
    def normalize_prices(self) -> 'DataPreprocessor':
        """
        Normalize prices to ensure they are valid numbers.
        
        Returns:
            DataPreprocessor: Self for method chaining
        """
        if 'price' in self.df.columns:
            self.df['price'] = pd.to_numeric(self.df['price'], errors='coerce')
            logger.info("Normalized prices")
        
        return self
    
    def add_text_features(self) -> 'DataPreprocessor':
        """
        Add combined text features for better embedding.
        Uses product_name, category, description; adds specifications, applications, manufacturer if present (e.g. AAW jobs).
        """
        base_cols = ['product_name', 'category', 'description']
        if all(col in self.df.columns for col in base_cols):
            combined = (
                self.df['product_name'].fillna('').astype(str) + ' ' +
                self.df['category'].fillna('').astype(str) + ' ' +
                self.df['description'].fillna('').astype(str)
            )
            if 'specifications' in self.df.columns:
                combined = combined + ' ' + self.df['specifications'].fillna('').astype(str)
            if 'applications' in self.df.columns:
                combined = combined + ' ' + self.df['applications'].fillna('').astype(str)
            if 'manufacturer' in self.df.columns:
                combined = combined + ' ' + self.df['manufacturer'].fillna('').astype(str)
            self.df['combined_text'] = combined.str.lower()
            logger.info("Added combined text feature")
        
        return self
    
    def get_processed_data(self) -> pd.DataFrame:
        """
        Get the processed DataFrame.
        
        Returns:
            pd.DataFrame: Processed DataFrame
        """
        return self.df
    
    def get_summary(self) -> dict:
        """
        Get a summary of preprocessing changes.
        
        Returns:
            dict: Summary of changes
        """
        return {
            'original_rows': len(self.original_df),
            'final_rows': len(self.df),
            'original_columns': len(self.original_df.columns),
            'final_columns': len(self.df.columns),
            'columns': self.df.columns.tolist(),
            'missing_values': self.df.isnull().sum().to_dict()
        }
    
    def preprocess_all(self) -> 'DataPreprocessor':
        """
        Apply all preprocessing steps.
        
        Returns:
            DataPreprocessor: Self for method chaining
        """
        self.clean_text_columns()
        self.remove_duplicates()
        self.handle_missing_values(strategy='drop')
        self.normalize_prices()
        self.add_text_features()
        logger.info("Completed all preprocessing steps")
        return self
