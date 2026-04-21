import json
import os


SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_SETTINGS = {
    "speech_rate": 175,
    "volume": 100,
    "weather_api_key": "",
    "news_api_key": "",
    "wake_word_enabled": False,
    "wake_word": "hey assip",
    "offline_voice_mode": False,
}


def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        return dict(DEFAULT_SETTINGS)
    try:
        with open(SETTINGS_PATH, "r") as f:
            data = json.load(f)
        settings = dict(DEFAULT_SETTINGS)
        settings.update(data if isinstance(data, dict) else {})
        return settings
    except Exception:
        return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    merged = dict(DEFAULT_SETTINGS)
    merged.update(settings if isinstance(settings, dict) else {})
    with open(SETTINGS_PATH, "w") as f:
        json.dump(merged, f, indent=4)
    return merged
