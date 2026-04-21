import threading
import tkinter as tk
from tkinter import messagebox, ttk

from assistant_preferences import load_settings, save_settings as save_assistant_settings
from ai_services import get_api_keys, set_api_keys
from command_router import process_command
from core_voice import set_voice_properties, speak, take_command, wish
from custom_commands import add_custom_command, list_custom_commands, remove_custom_command
from task_manager import pop_due_tasks
from usage_tracker import get_usage_summary


root = None
start_button = None
status_label = None
_update_status = None


def refresh_custom_commands_list(listbox):
    listbox.delete(0, tk.END)
    for item in list_custom_commands():
        phrase = item.get("phrase", "")
        action = item.get("action", "")
        listbox.insert(tk.END, f"{phrase} => {action}")


def show_custom_commands():
    window = tk.Toplevel(root)
    window.title("Custom Commands")
    window.geometry("500x420")
    ttk.Label(window, text="Custom Command Training", font=("Helvetica", 14, "bold")).pack(pady=10)
    listbox = tk.Listbox(window, height=12)
    listbox.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)
    refresh_custom_commands_list(listbox)
    form = ttk.Frame(window)
    form.pack(fill=tk.X, padx=10, pady=8)
    ttk.Label(form, text="Phrase").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    phrase_var = tk.StringVar()
    phrase_entry = ttk.Entry(form, textvariable=phrase_var, width=30)
    phrase_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
    ttk.Label(form, text="Action").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    action_type_var = tk.StringVar(value="open_app")
    action_type_combo = ttk.Combobox(
        form,
        textvariable=action_type_var,
        state="readonly",
        values=["open_app", "open_website", "web_search", "say", "system_info", "internet_speed"],
        width=16,
    )
    action_type_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
    ttk.Label(form, text="Value").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    value_var = tk.StringVar()
    value_entry = ttk.Entry(form, textvariable=value_var, width=30)
    value_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
    form.columnconfigure(1, weight=1)

    def save_custom():
        phrase = phrase_var.get().strip().lower()
        action_type = action_type_var.get().strip()
        value = value_var.get().strip()
        if not phrase:
            messagebox.showwarning("Custom Commands", "Phrase is required.")
            return
        if action_type in {"system_info", "internet_speed"}:
            action = action_type
        else:
            if not value:
                messagebox.showwarning("Custom Commands", "Value is required for selected action.")
                return
            action = f"{action_type}:{value}"
        add_custom_command(phrase, action)
        refresh_custom_commands_list(listbox)
        phrase_var.set("")
        value_var.set("")

    def remove_selected():
        selected = listbox.curselection()
        if not selected:
            return
        line = listbox.get(selected[0])
        phrase = line.split("=>")[0].strip()
        remove_custom_command(phrase)
        refresh_custom_commands_list(listbox)

    controls = ttk.Frame(window)
    controls.pack(fill=tk.X, padx=10, pady=8)
    ttk.Button(controls, text="Save Command", command=save_custom).pack(side=tk.LEFT, padx=5)
    ttk.Button(controls, text="Delete Selected", command=remove_selected).pack(side=tk.LEFT, padx=5)


def show_settings():
    settings = load_settings()
    weather_api_key, news_api_key = get_api_keys()
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("360x520")
    settings_window.resizable(False, False)
    ttk.Label(settings_window, text="Assistant Settings", font=("Helvetica", 14, "bold")).pack(pady=10)
    voice_frame = ttk.LabelFrame(settings_window, text="Voice Settings")
    voice_frame.pack(fill=tk.X, padx=10, pady=5, ipady=5)
    ttk.Label(voice_frame, text="Speech Rate:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    speed_var = tk.IntVar(value=int(settings.get("speech_rate", 175)))
    speed_scale = ttk.Scale(voice_frame, from_=100, to=250, variable=speed_var, orient=tk.HORIZONTAL)
    speed_scale.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
    ttk.Label(voice_frame, textvariable=speed_var).grid(row=0, column=2, padx=5, pady=5)
    ttk.Label(voice_frame, text="Volume:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
    volume_var = tk.IntVar(value=int(settings.get("volume", 100)))
    volume_scale = ttk.Scale(voice_frame, from_=0, to=100, variable=volume_var, orient=tk.HORIZONTAL)
    volume_scale.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
    ttk.Label(voice_frame, textvariable=volume_var).grid(row=1, column=2, padx=5, pady=5)
    api_frame = ttk.LabelFrame(settings_window, text="API Settings")
    api_frame.pack(fill=tk.X, padx=10, pady=5, ipady=5)
    ttk.Label(api_frame, text="Weather API Key:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    weather_api_entry = ttk.Entry(api_frame, width=20)
    weather_api_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
    weather_api_entry.insert(0, weather_api_key if weather_api_key else "")
    ttk.Label(api_frame, text="News API Key:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
    news_api_entry = ttk.Entry(api_frame, width=20)
    news_api_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
    news_api_entry.insert(0, news_api_key if news_api_key else "")
    mode_frame = ttk.LabelFrame(settings_window, text="Voice Behavior")
    mode_frame.pack(fill=tk.X, padx=10, pady=5, ipady=5)
    wake_word_enabled_var = tk.BooleanVar(value=bool(settings.get("wake_word_enabled", True)))
    offline_voice_var = tk.BooleanVar(value=bool(settings.get("offline_voice_mode", False)))
    wake_word_var = tk.StringVar(value=str(settings.get("wake_word", "hey assip")))
    ttk.Checkbutton(mode_frame, text="Enable Wake Word", variable=wake_word_enabled_var).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
    ttk.Checkbutton(mode_frame, text="Offline Voice Mode", variable=offline_voice_var).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
    ttk.Label(mode_frame, text="Wake Word:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
    wake_word_entry = ttk.Entry(mode_frame, textvariable=wake_word_var, width=20)
    wake_word_entry.grid(row=3, column=0, padx=5, pady=5, sticky=tk.EW)
    usage_frame = ttk.LabelFrame(settings_window, text="Usage")
    usage_frame.pack(fill=tk.X, padx=10, pady=5, ipady=5)
    ttk.Label(usage_frame, text=get_usage_summary(), wraplength=320).pack(padx=8, pady=6)
    ttk.Button(
        settings_window,
        text="Save Settings",
        command=lambda: save_settings(
            speed_var.get(),
            volume_var.get(),
            weather_api_entry.get(),
            news_api_entry.get(),
            wake_word_enabled_var.get(),
            wake_word_var.get(),
            offline_voice_var.get(),
            settings_window,
        ),
    ).pack(pady=10)


def save_settings(speed, volume, weather_api, news_api, wake_word_enabled, wake_word, offline_voice_mode, window):
    try:
        settings = {
            "speech_rate": speed,
            "volume": volume,
            "weather_api_key": weather_api,
            "news_api_key": news_api,
            "wake_word_enabled": bool(wake_word_enabled),
            "wake_word": str(wake_word).strip().lower() or "hey assip",
            "offline_voice_mode": bool(offline_voice_mode),
        }
        save_assistant_settings(settings)
        set_voice_properties(speed, volume)
        set_api_keys(weather_api, news_api)
        messagebox.showinfo("Settings", "Settings saved successfully!")
        window.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save settings: {str(e)}")


def update_status(status="ready"):
    if _update_status:
        _update_status(status)


def run_assistant():
    try:
        wish()
        while True:
            due_tasks = pop_due_tasks()
            for task in due_tasks:
                speak(f"Task reminder: {task.get('title', 'task')}")
            update_status("listening")
            settings = load_settings()
            offline_mode = bool(settings.get("offline_voice_mode", False))
            wake_enabled = bool(settings.get("wake_word_enabled", True))
            wake_word = str(settings.get("wake_word", "hey assip")).strip().lower()
            command = take_command(offline_only=offline_mode)
            if command:
                cmd = command.strip().lower()
                if wake_enabled:
                    if not cmd.startswith(wake_word):
                        continue
                    cmd = cmd[len(wake_word):].strip(" ,.!?")
                    if not cmd:
                        speak("Yes?")
                        continue
                update_status("processing")
                process_command(cmd)
                update_status("ready")
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        print(error_msg)
        root.after(0, lambda: messagebox.showerror("Error", error_msg))
        root.after(0, lambda: start_button.configure(state="normal"))
        root.after(0, lambda: update_status("ready"))


def start_assistant():
    try:
        start_button.configure(state="disabled")
        update_status("listening")
        assistant_thread = threading.Thread(target=run_assistant)
        assistant_thread.daemon = True
        assistant_thread.start()
    except Exception as e:
        error_msg = f"Error starting assistant: {str(e)}"
        print(error_msg)
        messagebox.showerror("Error", error_msg)
        start_button.configure(state="normal")
        update_status("ready")


def create_gui():
    global root, start_button, status_label, _update_status
    root = tk.Tk()
    root.title("AI Assistant")
    root.geometry("400x350")
    bg_color = "#f0f0f0"
    accent_color = "#4a86e8"
    text_color = "#333333"
    root.configure(bg=bg_color)
    style = ttk.Style()
    style.configure("TButton", padding=10, font=("Helvetica", 12))
    style.configure("Accent.TButton", background=accent_color)
    style.configure("TLabel", background=bg_color, foreground=text_color, font=("Helvetica", 10))
    style.configure("Title.TLabel", background=bg_color, foreground=text_color, font=("Helvetica", 16, "bold"))
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    title_label = ttk.Label(main_frame, text="AI Desktop Assistant", style="Title.TLabel")
    title_label.pack(pady=10)
    status_frame = ttk.Frame(main_frame)
    status_frame.pack(fill=tk.X, pady=10)
    status_label = ttk.Label(status_frame, text="Status: Ready", style="TLabel")
    status_label.pack(side=tk.LEFT, padx=5)
    status_canvas = tk.Canvas(status_frame, width=15, height=15, bg=bg_color, highlightthickness=0)
    status_canvas.pack(side=tk.LEFT)
    status_indicator = status_canvas.create_oval(2, 2, 13, 13, fill="gray")
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(expand=True)
    start_button = ttk.Button(button_frame, text="Start Assistant", command=start_assistant, style="Accent.TButton")
    start_button.pack(pady=10)
    settings_button = ttk.Button(button_frame, text="Settings", command=show_settings, style="TButton")
    settings_button.pack(pady=10)
    custom_button = ttk.Button(button_frame, text="Custom Commands", command=show_custom_commands, style="TButton")
    custom_button.pack(pady=10)
    quit_button = ttk.Button(button_frame, text="Quit", command=root.destroy, style="TButton")
    quit_button.pack(pady=10)
    version_label = ttk.Label(main_frame, text="v1.0.0", style="TLabel")
    version_label.pack(side=tk.BOTTOM, pady=5)

    def _local_update_status(status="ready"):
        if status == "listening":
            status_canvas.itemconfig(status_indicator, fill="green")
            status_label.config(text="Status: Listening")
        elif status == "processing":
            status_canvas.itemconfig(status_indicator, fill="orange")
            status_label.config(text="Status: Processing")
        elif status == "speaking":
            status_canvas.itemconfig(status_indicator, fill="blue")
            status_label.config(text="Status: Speaking")
        else:
            status_canvas.itemconfig(status_indicator, fill="gray")
            status_label.config(text="Status: Ready")

    _update_status = _local_update_status
    root.mainloop()


if __name__ == "__main__":
    create_gui()
        
