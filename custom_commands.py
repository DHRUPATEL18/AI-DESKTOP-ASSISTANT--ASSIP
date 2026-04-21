import json
import os


CUSTOM_COMMANDS_PATH = os.path.join(os.path.dirname(__file__), "custom_commands.json")


def _load():
    if not os.path.exists(CUSTOM_COMMANDS_PATH):
        return []
    try:
        with open(CUSTOM_COMMANDS_PATH, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def _save(data):
    with open(CUSTOM_COMMANDS_PATH, "w") as f:
        json.dump(data, f, indent=2)


def list_custom_commands():
    return _load()


def add_custom_command(phrase, action):
    phrase = str(phrase).strip().lower()
    action = str(action).strip()
    if not phrase or not action:
        return None
    data = _load()
    for item in data:
        if item.get("phrase") == phrase:
            item["action"] = action
            _save(data)
            return item
    item = {"phrase": phrase, "action": action}
    data.append(item)
    _save(data)
    return item


def remove_custom_command(phrase):
    phrase = str(phrase).strip().lower()
    data = _load()
    filtered = [item for item in data if item.get("phrase") != phrase]
    if len(filtered) == len(data):
        return False
    _save(filtered)
    return True


def find_action(command_text):
    command_text = str(command_text).strip().lower()
    for item in _load():
        phrase = str(item.get("phrase", "")).strip().lower()
        if phrase and (command_text == phrase or command_text.startswith(phrase + " ")):
            return item.get("action", "")
    return None
