import re
import os
import shutil

import psutil

from ai_services import (
    extract_category,
    get_api_keys,
    get_chat_response,
    get_daily_news,
    get_weather,
    open_website,
    search_wikipedia,
    web_search,
)
from core_voice import speak, take_command
from custom_commands import find_action
from messaging_services import send_sos_sms, send_whatsapp_message
from nlp_processor import process_nlp
from system_services import (
    adjust_volume,
    check_internet_speed,
    get_ip_mac,
    get_system_info,
    open_app,
    open_file_explorer,
    process_system_control,
    set_reminder,
)
from task_manager import add_task, complete_task, delete_task, list_tasks
from usage_tracker import get_usage_summary, log_event


def execute_custom_action(action):
    action = str(action).strip()
    if not action:
        return False
    lowered = action.lower()
    if lowered == "system_info":
        get_system_info()
        return True
    if lowered == "internet_speed":
        check_internet_speed()
        return True
    if lowered.startswith("open_app:"):
        app_name = action.split(":", 1)[1].strip()
        open_app(app_name)
        speak(f"Opening {app_name}")
        log_event("app", app_name)
        return True
    if lowered.startswith("open_website:"):
        website = action.split(":", 1)[1].strip()
        open_website(website)
        return True
    if lowered.startswith("web_search:"):
        query = action.split(":", 1)[1].strip()
        web_search(query)
        return True
    if lowered.startswith("say:"):
        text = action.split(":", 1)[1].strip()
        speak(text)
        return True
    return False


def process_command(command):
    if not command:
        speak("I didn't hear anything. Please try again.")
        return

    normalized_command = command.lower().strip()
    log_event("command", normalized_command)

    usage_match = re.search(r"(app|assistant|usage)\s+(report|summary|stats|statistics)", normalized_command)
    if usage_match:
        summary = get_usage_summary()
        speak(summary)
        return

    add_task_match = re.search(r"(?:add|create)\s+(?:task|todo)\s+(.+?)(?:\s+in\s+(\d+)\s+minutes?)?(?:\?|$)", normalized_command)
    if add_task_match:
        title = add_task_match.group(1).strip()
        minutes = add_task_match.group(2)
        task = add_task(title, minutes=minutes)
        due_text = f" due in {minutes} minutes" if minutes else ""
        speak(f"Task {task['id']} added{due_text}: {task['title']}")
        return

    list_task_match = re.search(r"(list|show|view)\s+(?:my\s+)?(?:tasks|todos)", normalized_command)
    if list_task_match:
        tasks = list_tasks()
        if not tasks:
            speak("You have no pending tasks.")
            return
        lines = [f"{t['id']}. {t['title']}" for t in tasks[:10]]
        speak("Your tasks are: " + " | ".join(lines))
        return

    complete_task_match = re.search(r"(?:complete|finish|done)\s+(?:task|todo)\s+(\d+)", normalized_command)
    if complete_task_match:
        task_id = int(complete_task_match.group(1))
        task = complete_task(task_id)
        if task:
            speak(f"Task {task_id} marked completed.")
        else:
            speak(f"Task {task_id} not found.")
        return

    delete_task_match = re.search(r"(?:delete|remove)\s+(?:task|todo)\s+(\d+)", normalized_command)
    if delete_task_match:
        task_id = int(delete_task_match.group(1))
        ok = delete_task(task_id)
        if ok:
            speak(f"Task {task_id} deleted.")
        else:
            speak(f"Task {task_id} not found.")
        return

    custom_action = find_action(normalized_command)
    if custom_action and execute_custom_action(custom_action):
        return

    volume_match = re.search(
        r"(?:set|change|adjust)?\s*(?:the\s*)?(volume|sound)(?:\s*(?:level|up|down)?)?\s*(?:to|at)?\s*(\d+)(?:\s*percent|%)?",
        normalized_command,
    )
    if volume_match:
        try:
            volume_level = int(volume_match.group(2))
            print(f"Setting volume to {volume_level}%")
            adjust_volume(volume_level)
            return
        except (ValueError, IndexError):
            speak("I couldn't understand the volume level. Please try again.")
            return

    if re.search(r"(volume|sound)\s+(up|increase|higher|louder)", normalized_command):
        adjust_volume(70)
        return

    if re.search(r"(volume|sound)\s+(down|decrease|lower|quieter)", normalized_command):
        adjust_volume(30)
        return

    if re.search(r"mute|quiet|silence", normalized_command):
        adjust_volume(0)
        return

    if re.search(r"(system|computer)\s+(info|information|status)", normalized_command):
        get_system_info()
        return

    if re.search(r"(cpu|processor)\s+(usage|info|status)", normalized_command):
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count(logical=False)
        speak(f"CPU usage is currently {cpu_percent}% across {cpu_count} physical cores.")
        return

    if re.search(r"(memory|ram)\s+(usage|info|status)", normalized_command):
        memory = psutil.virtual_memory()
        memory_total = round(memory.total / (1024**3), 2)
        memory_used = round(memory.used / (1024**3), 2)
        speak(f"Memory usage is {memory.percent}%. {memory_used} gigabytes used out of {memory_total} gigabytes total.")
        return

    if re.search(r"(disk|storage|drive)\s+(usage|info|status)", normalized_command):
        home_path = os.path.expanduser("~")
        disk_usage = shutil.disk_usage(home_path)
        disk_total = round(disk_usage.total / (1024**3), 2)
        disk_used = round(disk_usage.used / (1024**3), 2)
        disk_percent = round((disk_usage.used / disk_usage.total) * 100, 2)
        speak(f"Disk usage is {disk_percent}%. {disk_used} gigabytes used out of {disk_total} gigabytes total.")
        return

    if re.search(r"(battery|power)\s+(level|status|info)", normalized_command):
        battery = psutil.sensors_battery()
        if battery:
            charging = "plugged in" if battery.power_plugged else "on battery power"
            speak(f"Battery is at {battery.percent}% and currently {charging}.")
        else:
            speak("Battery information is not available.")
        return

    screenshot_match = re.search(r"(?:take|grab|capture)\s+(?:a\s+)?screenshot", normalized_command)
    if screenshot_match:
        try:
            from pywhatkit import take_screenshot
            take_screenshot()
            speak("Screenshot taken successfully.")
        except Exception as e:
            speak(f"I couldn't take a screenshot. {str(e)}")
        return

    search_match = re.search(r"(?:search|look\s+(?:up|for)|find|google)\s+(?:for\s+)?(.*)", normalized_command)
    if search_match:
        search_query = search_match.group(1).strip()
        if search_query:
            web_search(search_query)
            return

    file_explorer_match = re.search(r"(open|launch|show)(?:\s+(?:the|my))?\s+(?:file(?:\s+)?(?:explorer|manager)|documents|files)", normalized_command)
    if file_explorer_match:
        open_file_explorer()
        return

    internet_speed_match = re.search(r"(check|test|what's|how's|measure)(?:\s+(?:the|my))?\s+(?:internet|network|wifi|wi-fi|connection)(?:\s+speed)?", normalized_command)
    if internet_speed_match:
        check_internet_speed()
        return

    reminder_match = re.search(r"(?:set|create|add|remind\s+me\s+(?:about|of))(?:\s+a)?\s+reminder\s+(?:for|about|to)?\s+(.+?)(?:\s+in\s+(\d+)\s+minutes?)?(?:\?|$|please)", normalized_command)
    if reminder_match:
        title = reminder_match.group(1).strip()
        minutes = reminder_match.group(2) if reminder_match.group(2) else "5"
        set_reminder(title, minutes)
        return

    nlp_result = process_nlp(normalized_command)
    intent = nlp_result["intent"]
    entities = nlp_result["entities"]

    if intent == "open_website" and "website" in entities:
        open_website(entities["website"])
    elif intent == "wikipedia" and "query" in entities:
        search_wikipedia(entities["query"])
    elif intent == "web_search" and "query" in entities:
        web_search(entities["query"])
    elif intent == "search" and "query" in entities:
        web_search(entities["query"])
    elif intent == "weather" and "city" in entities:
        get_weather(entities["city"])
    elif intent == "news":
        _, news_api_key = get_api_keys()
        category = entities.get("category", extract_category(normalized_command))
        get_daily_news(news_api_key, category=category)
    elif intent == "system_info":
        get_ip_mac()
    elif intent == "whatsapp" and "contact" in entities:
        message = entities.get("message", "")
        if not message:
            speak("What message would you like to send?")
            message = take_command()
        send_whatsapp_message(entities["contact"], message)
    elif intent == "emergency":
        send_sos_sms()
    elif intent == "app_control" and "app_name" in entities:
        try:
            open_app(entities["app_name"])
            log_event("app", entities["app_name"])
            speak(f"Opening {entities['app_name']}")
        except Exception as e:
            speak(f"I couldn't open {entities['app_name']}. {e}")
    elif intent == "system_control":
        process_system_control(command, entities)
    elif intent == "file_explorer":
        path = entities.get("path", None)
        open_file_explorer(path)
    elif intent == "internet_speed":
        check_internet_speed()
    elif intent == "set_reminder":
        title = entities.get("title", "reminder")
        minutes = entities.get("minutes", 5)
        set_reminder(title, minutes)
    else:
        get_chat_response(command)
