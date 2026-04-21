import os
import platform
import re
import shutil
import socket
import subprocess
import threading
import time
import uuid
from tkinter import messagebox

import psutil
import pyautogui
import screen_brightness_control as sbc

from core_voice import speak


def get_ip_mac():
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        mac_address = ":".join(re.findall("..", "%012x" % uuid.getnode()))
        result = f"IP Address: {ip_address}\nMAC Address: {mac_address}"
        print(result)
        speak(result)
        return result
    except Exception as e:
        speak("I couldn't retrieve the IP and MAC address.")
        print(f"Error: {e}")
        return ""


def get_system_info():
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count(logical=False)
    cpu_logical = psutil.cpu_count(logical=True)
    memory = psutil.virtual_memory()
    memory_total = round(memory.total / (1024**3), 2)
    memory_used = round(memory.used / (1024**3), 2)
    memory_percent = memory.percent
    home_path = os.path.expanduser("~")
    disk_usage = shutil.disk_usage(home_path)
    disk_total = round(disk_usage.total / (1024**3), 2)
    disk_used = round(disk_usage.used / (1024**3), 2)
    disk_percent = round((disk_usage.used / disk_usage.total) * 100, 2)
    battery_info = "Not available"
    battery = psutil.sensors_battery()
    if battery:
        battery_percent = battery.percent
        charging = "Plugged In" if battery.power_plugged else "On Battery"
        battery_info = f"{battery_percent}% ({charging})"
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    info = f"""
    System Information:
    CPU: {cpu_percent}% usage across {cpu_logical} logical cores ({cpu_count} physical)
    Memory: {memory_used}GB used out of {memory_total}GB ({memory_percent}%)
    Storage: {disk_used}GB used out of {disk_total}GB ({disk_percent}%)
    Network: IP address {ip_address} on {hostname}
    Battery: {battery_info}
    """
    print(info)
    speak(f"Here's your system information. CPU usage is {cpu_percent}%, memory usage is {memory_percent}%, and disk usage is {disk_percent}%. Battery is {battery_info}.")
    return info


def adjust_brightness(level):
    try:
        if 0 <= level <= 100:
            sbc.set_brightness(level)
            speak(f"Brightness set to {level}%")
        else:
            speak("Brightness level should be between 0 and 100")
    except Exception as e:
        speak(f"Sorry, I couldn't adjust the brightness. {str(e)}")


def adjust_volume(level):
    try:
        if 0 <= level <= 100:
            pyautogui.press("volumemute")
            time.sleep(0.5)
            steps = int(level / 2)
            if steps < 0:
                steps = 0
            elif steps > 50:
                steps = 50
            pyautogui.press("volumemute")
            time.sleep(0.2)
            for _ in range(steps):
                pyautogui.press("volumeup")
                time.sleep(0.05)
            speak(f"Volume set to {level}%")
        else:
            speak("Volume level should be between 0 and 100")
    except Exception as e:
        print(f"Error adjusting volume: {e}")
        speak(f"Sorry, I couldn't adjust the volume. {str(e)}")


def process_system_control(command, entities):
    if "brightness" in entities:
        adjust_brightness(entities["brightness"])
        return True
    if "volume" in entities:
        adjust_volume(entities["volume"])
        return True
    if re.search(r"(cpu|processor)", command.lower()):
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count(logical=False)
        speak(f"CPU usage is currently {cpu_percent}% across {cpu_count} physical cores.")
        return True
    if re.search(r"(memory|ram)", command.lower()):
        memory = psutil.virtual_memory()
        memory_total = round(memory.total / (1024**3), 2)
        memory_used = round(memory.used / (1024**3), 2)
        speak(f"Memory usage is {memory.percent}%. {memory_used} gigabytes used out of {memory_total} gigabytes total.")
        return True
    if re.search(r"(disk|storage|drive)", command.lower()):
        home_path = os.path.expanduser("~")
        disk_usage = shutil.disk_usage(home_path)
        disk_total = round(disk_usage.total / (1024**3), 2)
        disk_used = round(disk_usage.used / (1024**3), 2)
        disk_percent = round((disk_usage.used / disk_usage.total) * 100, 2)
        speak(f"Disk usage is {disk_percent}%. {disk_used} gigabytes used out of {disk_total} gigabytes total.")
        return True
    if re.search(r"(battery|power)", command.lower()):
        battery = psutil.sensors_battery()
        if battery:
            charging = "plugged in" if battery.power_plugged else "on battery power"
            speak(f"Battery is at {battery.percent}% and currently {charging}.")
        else:
            speak("Battery information is not available.")
        return True
    if re.search(r"(network|internet|ip|connection)", command.lower()):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        speak(f"Your device name is {hostname} with IP address {ip_address}.")
        return True
    get_system_info()
    return True


def open_file_explorer(path=None):
    try:
        if not path:
            path = os.path.expanduser("~")
        if platform.system() == "Windows":
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])
        speak(f"Opening file explorer at {path}")
    except Exception as e:
        speak(f"I couldn't open the file explorer. {str(e)}")


def open_app(app_name):
    app = app_name.strip()
    system_root = os.environ.get("SystemRoot", "C:\\Windows")
    pf = os.environ.get("ProgramFiles", "C:\\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
    appdata = os.environ.get("APPDATA", "")
    localappdata = os.environ.get("LocalAppData", "")
    exe_paths = []
    if app.lower() in ["notepad"]:
        exe_paths.append(os.path.join(system_root, "System32", "notepad.exe"))
    if app.lower() in ["mspaint", "paint"]:
        exe_paths.append(os.path.join(system_root, "System32", "mspaint.exe"))
    if app.lower() in ["cmd", "command prompt"]:
        exe_paths.append(os.path.join(system_root, "System32", "cmd.exe"))
    if app.lower() in ["chrome"]:
        exe_paths.append(os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"))
        exe_paths.append(os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"))
    if app.lower() in ["msedge", "edge", "browser"]:
        exe_paths.append(os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe"))
        exe_paths.append(os.path.join(pf86, "Microsoft", "Edge", "Application", "msedge.exe"))
    if app.lower() in ["winword", "word"]:
        exe_paths.append(os.path.join(pf, "Microsoft Office", "root", "Office16", "WINWORD.EXE"))
        exe_paths.append(os.path.join(pf86, "Microsoft Office", "root", "Office16", "WINWORD.EXE"))
    if app.lower() in ["excel"]:
        exe_paths.append(os.path.join(pf, "Microsoft Office", "root", "Office16", "EXCEL.EXE"))
        exe_paths.append(os.path.join(pf86, "Microsoft Office", "root", "Office16", "EXCEL.EXE"))
    if app.lower() in ["powerpnt", "powerpoint"]:
        exe_paths.append(os.path.join(pf, "Microsoft Office", "root", "Office16", "POWERPNT.EXE"))
        exe_paths.append(os.path.join(pf86, "Microsoft Office", "root", "Office16", "POWERPNT.EXE"))
    if app.lower() in ["spotify"]:
        if appdata:
            exe_paths.append(os.path.join(appdata, "Spotify", "Spotify.exe"))
        if localappdata:
            exe_paths.append(os.path.join(localappdata, "Microsoft", "WindowsApps", "Spotify.exe"))
    if app.lower() in ["whatsapp", "watsapp"]:
        if localappdata:
            exe_paths.append(os.path.join(localappdata, "WhatsApp", "WhatsApp.exe"))
        exe_paths.append(os.path.join(os.path.expanduser("~"), "AppData", "Local", "WhatsApp", "WhatsApp.exe"))
    if app.lower() in ["chatgpt"]:
        if localappdata:
            exe_paths.append(os.path.join(localappdata, "Programs", "ChatGPT", "ChatGPT.exe"))
        exe_paths.append(os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "ChatGPT", "ChatGPT.exe"))
    for p in exe_paths:
        if os.path.exists(p):
            os.startfile(p)
            return True
    if app.lower() in ["facebook", "fb"]:
        import webbrowser
        webbrowser.open("https://www.facebook.com/")
        return True
    if app.lower() in ["instagram", "insta"]:
        import webbrowser
        webbrowser.open("https://www.instagram.com/")
        return True
    if app.lower() in ["spotify"]:
        subprocess.Popen('start "" spotify:', shell=True)
        return True
    if app.lower() in ["whatsapp", "watsapp"]:
        import webbrowser
        webbrowser.open("https://web.whatsapp.com/")
        return True
    if app.lower() in ["chatgpt"]:
        import webbrowser
        webbrowser.open("https://chatgpt.com/")
        return True
    subprocess.Popen(f'start "" {app}', shell=True)
    return True


def check_internet_speed():
    try:
        speak("Testing your internet speed. This might take a few seconds...")
        host = "www.google.com"
        ping_result = subprocess.run(
            ["ping", "-n", "4", host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if ping_result.returncode == 0:
            result = ping_result.stdout
            avg_line = [line for line in result.split("\n") if "Average" in line]
            if avg_line:
                avg_time = avg_line[0].split("=")[-1].strip()
                speak(f"Your internet connection is working. Average ping time to Google is {avg_time}.")
            else:
                speak("Your internet connection is working, but I couldn't determine the speed.")
        else:
            speak("I couldn't reach the internet. Please check your connection.")
    except Exception as e:
        speak(f"I couldn't test your internet speed. {str(e)}")


def set_reminder(title, minutes):
    try:
        minutes = int(minutes)
        speak(f"Setting a reminder for {title} in {minutes} minutes.")

        def reminder_callback():
            messagebox.showinfo("Reminder", f"Reminder: {title}")
            speak(f"Reminder: {title}")

        threading.Timer(minutes * 60, reminder_callback).start()
    except Exception as e:
        speak(f"I couldn't set the reminder. {str(e)}")
