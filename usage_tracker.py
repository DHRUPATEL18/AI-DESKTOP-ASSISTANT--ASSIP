import json
import os
from datetime import datetime


USAGE_PATH = os.path.join(os.path.dirname(__file__), "usage_log.json")


def _load_usage():
    if not os.path.exists(USAGE_PATH):
        return {"events": []}
    try:
        with open(USAGE_PATH, "r") as f:
            data = json.load(f)
        if isinstance(data, dict) and "events" in data and isinstance(data["events"], list):
            return data
    except Exception:
        pass
    return {"events": []}


def _save_usage(data):
    with open(USAGE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def log_event(event_type, name):
    data = _load_usage()
    data["events"].append(
        {
            "event_type": str(event_type),
            "name": str(name),
            "timestamp": datetime.now().isoformat(),
        }
    )
    _save_usage(data)


def get_usage_summary():
    data = _load_usage()
    events = data["events"]
    if not events:
        return "No usage activity recorded yet."
    app_counts = {}
    command_counts = {}
    for event in events:
        et = event.get("event_type", "")
        name = event.get("name", "")
        if et == "app":
            app_counts[name] = app_counts.get(name, 0) + 1
        if et == "command":
            command_counts[name] = command_counts.get(name, 0) + 1
    top_apps = sorted(app_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_commands = sorted(command_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    parts = []
    if top_apps:
        parts.append("Top apps: " + ", ".join([f"{name} ({count})" for name, count in top_apps]))
    if top_commands:
        parts.append("Top commands: " + ", ".join([f"{name} ({count})" for name, count in top_commands]))
    if not parts:
        return "No summarized usage available yet."
    return " | ".join(parts)
