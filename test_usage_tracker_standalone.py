import os
import json
from usage_tracker import log_event, get_usage_summary, USAGE_PATH

def test_usage_tracker():
    print("--- Testing usage_tracker.py ---")
    
    # 1. Log a unique test event
    test_app = "TestApp_123"
    print(f"Logging test event: {test_app}...")
    log_event("app", test_app)
    
    # 2. Check if usage_log.json was updated
    if os.path.exists(USAGE_PATH):
        with open(USAGE_PATH, "r") as f:
            data = json.load(f)
            events = data.get("events", [])
            found = any(e.get("name") == test_app for e in events)
            if found:
                print("SUCCESS: Event found in usage_log.json")
            else:
                print("FAILED: Event not found in usage_log.json")
    else:
        print(f"FAILED: {USAGE_PATH} does not exist.")
        return

    # 3. Test summary generation
    print("Generating usage summary...")
    summary = get_usage_summary()
    print(f"Summary: {summary}")
    
    if test_app in summary:
        print("SUCCESS: Summary contains the test event.")
    else:
        print("FAILED: Summary does not contain the test event.")

    print("--- Testing Complete ---")

if __name__ == "__main__":
    test_usage_tracker()
