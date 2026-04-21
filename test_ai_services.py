import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import ai_services

class TestAIServices(unittest.TestCase):

    @patch('ai_services.requests.get')
    @patch('ai_services.speak')
    def test_weather_no_key(self, mock_speak, mock_get):
        """Test weather service with no API key."""
        # Set API key to something invalid/empty
        ai_services.WEATHER_API_KEY = ""
        result = ai_services.get_weather("London")
        self.assertIn("add a valid Weather API key", result)
        mock_speak.assert_called()

    @patch('ai_services.wikipedia.summary')
    @patch('ai_services.speak')
    def test_wikipedia_search(self, mock_speak, mock_wiki_summary):
        """Test wikipedia search."""
        mock_wiki_summary.return_value = "Python is a programming language."
        ai_services.search_wikipedia("Python")
        mock_speak.assert_called_with("Python is a programming language.")

    def test_extract_category(self):
        """Test news category extraction."""
        self.assertEqual(ai_services.extract_category("what's the latest in cricket"), "sports")
        self.assertEqual(ai_services.extract_category("how is the economy"), "business")
        self.assertEqual(ai_services.extract_category("tell me something random"), "general")

if __name__ == "__main__":
    unittest.main()
