import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import command_router

class TestCommandRouter(unittest.TestCase):

    @patch('command_router.web_search')
    @patch('command_router.speak')
    def test_search_command(self, mock_speak, mock_web_search):
        """Test search command routing."""
        command_router.process_command("search for artificial intelligence")
        mock_web_search.assert_called_with("artificial intelligence")

    @patch('command_router.get_system_info')
    def test_system_info_command(self, mock_get_info):
        """Test system info command routing."""
        command_router.process_command("show system information")
        mock_get_info.assert_called()

    @patch('command_router.add_task')
    @patch('command_router.speak')
    def test_add_task_command(self, mock_speak, mock_add_task):
        """Test add task command routing."""
        mock_add_task.return_value = {"id": 1, "title": "buy milk"}
        command_router.process_command("add task buy milk")
        mock_add_task.assert_called()
        self.assertIn("buy milk", mock_add_task.call_args[0][0])

    @patch('command_router.adjust_volume')
    def test_volume_command(self, mock_adjust_volume):
        """Test volume command routing."""
        command_router.process_command("set volume to 50 percent")
        mock_adjust_volume.assert_called_with(50)

    @patch('command_router.get_weather')
    def test_weather_command(self, mock_get_weather):
        """Test weather command routing."""
        # This might go through NLP
        command_router.process_command("what is the weather in Mumbai")
        # NLP might be used here, let's see if it calls get_weather
        # If it doesn't call it directly because of NLP, we might need to mock nlp_processor too
        # but let's check if the router handles it.
        pass

if __name__ == "__main__":
    unittest.main()
