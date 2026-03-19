import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json

# Add 'src' to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Mock Config before importing chatbot
class MockConfig:
    MONGO_URI = "mongodb://localhost:27017"
    MONGO_DB = "test_db"
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama3.2"

with patch('src.api.routes.chatbot.Config', MockConfig):
    from src.api.routes.chatbot import _ollama_available, _gather_system_context

class TestChatbotLogic(unittest.TestCase):
    
    @patch('urllib.request.urlopen')
    def test_ollama_available_success(self, mock_urlopen):
        # Mock successful response from /api/tags
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "models": [{"name": "llama3.2:latest"}]
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # We need to re-patch Config inside the function if it's used globally
        with patch('src.api.routes.chatbot.OLLAMA_BASE', "http://localhost:11434"):
            with patch('src.api.routes.chatbot.OLLAMA_MODEL', "llama3.2"):
                result = _ollama_available()
                self.assertTrue(result)

    @patch('urllib.request.urlopen')
    def test_ollama_available_failure(self, mock_urlopen):
        # Mock connection failure
        mock_urlopen.side_effect = Exception("Connection refused")
        
        with patch('src.api.routes.chatbot.OLLAMA_BASE', "http://localhost:11434"):
            result = _ollama_available()
            self.assertFalse(result)

    @patch('src.api.routes.chatbot._col')
    def test_gather_context(self, mock_col):
        # Mock MongoDB collections
        mock_users = MagicMock()
        mock_users.count_documents.return_value = 10
        mock_users.find.return_value.sort.return_value.limit.return_value = []
        
        mock_jobs = MagicMock()
        mock_jobs.count_documents.return_value = 5
        mock_jobs.find.return_value.sort.return_value.limit.return_value = []
        
        mock_history = MagicMock()
        mock_history.count_documents.return_value = 20
        
        def side_effect(name):
            if name == "users": return mock_users
            if name == "jobs": return mock_jobs
            if name == "history": return mock_history
            return MagicMock()
            
        mock_col.side_effect = side_effect
        
        ctx = _gather_system_context()
        self.assertEqual(ctx["total_users"], 10)
        self.assertEqual(ctx["total_jobs"], 5)
        self.assertEqual(ctx["total_sessions"], 20)

if __name__ == '__main__':
    unittest.main()
