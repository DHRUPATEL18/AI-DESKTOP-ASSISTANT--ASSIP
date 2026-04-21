import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modular components
import task_manager
import usage_tracker
import assistant_preferences
import nlp_processor
import core_voice

class TestAssipAssistant(unittest.TestCase):

    def test_task_manager(self):
        """Test adding, listing, and completing tasks."""
        # Clear tasks for testing if possible or use a temp file
        # For now, just test basic logic
        task = task_manager.add_task("Test Task", minutes=1)
        self.assertEqual(task["title"], "Test Task")
        self.assertFalse(task["completed"])
        
        tasks = task_manager.list_tasks()
        self.assertTrue(any(t["id"] == task["id"] for t in tasks))
        
        completed_task = task_manager.complete_task(task["id"])
        self.assertTrue(completed_task["completed"])
        
        task_manager.delete_task(task["id"])

    def test_usage_tracker(self):
        """Test logging and summary."""
        usage_tracker.log_event("test_event", "test_name")
        summary = usage_tracker.get_usage_summary()
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary) > 0)

    def test_preferences(self):
        """Test loading and saving settings."""
        settings = assistant_preferences.load_settings()
        self.assertIn("speech_rate", settings)
        
        original_rate = settings["speech_rate"]
        settings["speech_rate"] = 200
        assistant_preferences.save_settings(settings)
        
        new_settings = assistant_preferences.load_settings()
        self.assertEqual(new_settings["speech_rate"], 200)
        
        # Restore
        settings["speech_rate"] = original_rate
        assistant_preferences.save_settings(settings)

    def test_nlp_processor(self):
        """Test intent classification."""
        # Test a few common phrases
        intent1, score1 = nlp_processor.classify_intent("what is the weather in London")
        self.assertEqual(intent1, "weather")
        
        intent2, score2 = nlp_processor.classify_intent("search for Python programming")
        self.assertEqual(intent2, "web_search")
        
        entities = nlp_processor.extract_entities("weather in Mumbai", "weather")
        self.assertEqual(entities.get("city"), "Mumbai")

    @patch('core_voice.engine')
    def test_core_voice_speak(self, mock_engine):
        """Test speak function with mocked engine."""
        core_voice.speak("Hello")
        # Since engine might be initialized globally, we check if say was called if engine exists
        if core_voice.engine:
            core_voice.engine.say.assert_called()

if __name__ == "__main__":
    unittest.main()
