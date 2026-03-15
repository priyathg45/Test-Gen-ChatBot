"""Tests for the chatbot."""
import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.loader import DataLoader
from src.data.preprocessor import DataPreprocessor
from src.config import Config

class TestDataLoader(unittest.TestCase):
    """Test cases for DataLoader."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.loader = DataLoader(Config.DATA_PATH)
    
    def test_load_data(self):
        """Test loading data from CSV."""
        df = self.loader.load()
        self.assertIsNotNone(df)
        self.assertGreater(len(df), 0)
    
    def test_get_data(self):
        """Test getting loaded data."""
        self.loader.load()
        df = self.loader.get_data()
        self.assertIsNotNone(df)
    
    def test_get_product_by_id(self):
        """Test getting product by ID."""
        self.loader.load()
        product = self.loader.get_product_by_id(1)
        self.assertIsNotNone(product)
        self.assertEqual(product['product_id'], 1)
    
    def test_search_products(self):
        """Test searching products."""
        self.loader.load()
        results = self.loader.search_products('window')
        self.assertGreater(len(results), 0)
    
    def test_get_stats(self):
        """Test getting dataset statistics."""
        self.loader.load()
        stats = self.loader.get_stats()
        self.assertIn('total_products', stats)
        self.assertIn('categories', stats)

class TestDataPreprocessor(unittest.TestCase):
    """Test cases for DataPreprocessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        loader = DataLoader(Config.DATA_PATH)
        self.df = loader.load()
        self.preprocessor = DataPreprocessor(self.df)
    
    def test_preprocess_all(self):
        """Test all preprocessing steps."""
        result = self.preprocessor.preprocess_all()
        self.assertIsNotNone(result)
        self.assertGreater(len(self.preprocessor.get_processed_data()), 0)
    
    def test_clean_text(self):
        """Test text cleaning."""
        text = "  test  text  "
        cleaned = self.preprocessor.clean_text(text)
        self.assertEqual(cleaned, "test text")
    
    def test_summary(self):
        """Test preprocessing summary."""
        self.preprocessor.preprocess_all()
        summary = self.preprocessor.get_summary()
        self.assertIn('original_rows', summary)
        self.assertIn('final_rows', summary)

if __name__ == '__main__':
    unittest.main()
