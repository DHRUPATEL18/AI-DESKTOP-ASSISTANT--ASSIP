import json
import os
from datetime import datetime, timedelta


TASKS_PATH = os.path.join(os.path.dirname(__file__), "tasks.json")


def _load_tasks():
    if not os.path.exists(TASKS_PATH):
        return []
    try:
        with open(TASKS_PATH, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def _save_tasks(tasks):
    with open(TASKS_PATH, "w") as f:
        json.dump(tasks, f, indent=2)


def add_task(title, minutes=None):
    tasks = _load_tasks()
    task_id = max([t.get("id", 0) for t in tasks], default=0) + 1
    due_at = None
    if minutes is not None:
        try:
            due_at = (datetime.now() + timedelta(minutes=int(minutes))).isoformat()
        except Exception:
            due_at = None
    task = {
        "id": task_id,
        "title": str(title).strip(),
        "created_at": datetime.now().isoformat(),
        "due_at": due_at,
        "completed": False,
        "notified": False,
    }
    tasks.append(task)
    _save_tasks(tasks)
    return task


def list_tasks(show_completed=False):
    tasks = _load_tasks()
    if show_completed:
        return tasks
    return [t for t in tasks if not t.get("completed", False)]


def complete_task(task_id):
    tasks = _load_tasks()
    for task in tasks:
        if task.get("id") == int(task_id):
            task["completed"] = True
            _save_tasks(tasks)
            return task
    return None


def delete_task(task_id):
    tasks = _load_tasks()
    filtered = [t for t in tasks if t.get("id") != int(task_id)]
    if len(filtered) == len(tasks):
        return False
    _save_tasks(filtered)
    return True


def pop_due_tasks():
    tasks = _load_tasks()
    due = []
    now = datetime.now()
    changed = False
    for task in tasks:
        if task.get("completed"):
            continue
        due_at = task.get("due_at")
        if not due_at:
            continue
        try:
            due_time = datetime.fromisoformat(due_at)
        except Exception:
            continue
        if due_time <= now and not task.get("notified", False):
            task["notified"] = True
            due.append(task)
            changed = True
    if changed:
        _save_tasks(tasks)
    return due
