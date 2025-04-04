import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox

PATH_FILE = "settings.json"  # Define path to settings file


def create_settings():
    """Creates settings.json if it doesn't exist, with an initial structure, and creates a folder called 'api_metadata'."""
    if not os.path.exists(PATH_FILE):
        with open(PATH_FILE, 'w', encoding="utf-8") as f:
            json.dump({"libraries": {"series": [], "movies": []}}, f, indent=4)
        print("[ info ] Created settings.json with default structure.")

    if not os.path.exists('api_metadata'):
        os.makedirs('api_metadata')
        print("[ info ] Created folder 'api_metadata'.")


    # Check if the file exists
    if not os.path.exists("watchdog_temp.txt"):
        # Create the file if it doesn't exist
        with open("watchdog_temp.txt", 'w') as file:
            file.write("This is a new file.")  # You can write any content here
        print(f"'watchdog_temp.txt' has been created.")

def delete_settings():
    if os.path.exists(PATH_FILE):
        os.remove(PATH_FILE)

def load_paths():
    """Load paths from settings.json into a dictionary, ensuring default structure."""
    try:
        with open(PATH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("[WARNING] settings.json is corrupted. Resetting file.")
        create_settings()  # Reset file if it contains invalid JSON
        return {"libraries": {}}

def save_paths(paths):
    """Save paths dictionary to settings.json."""
    with open(PATH_FILE, "w", encoding="utf-8") as f:
        json.dump(paths, f, indent=4)

def check_duplicates(PATH, media_type, folder_path):
    """Check if the path already exists to prevent duplicates."""
    if folder_path in PATH["libraries"].get(media_type, []):
        messagebox.showinfo("Duplicate Path", "This folder is already added.")
        return True  # Prevent duplicate paths
    return False

def create_or_update_path(category, folder_path):
    """Allow users to add multiple unique paths per media type."""

    if not folder_path:
        messagebox.showwarning("No Selection", "No folder selected. Action cancelled.")
        return None

    # Load or create settings
    PATH = load_paths()

    # Ensure media type exists in JSON structure
    if category not in PATH["libraries"]:
        PATH["libraries"][category] = []

    # Check for duplicates before adding
    if check_duplicates(PATH, category, folder_path):
        return None

    # Add new path and save
    PATH["libraries"][category].append(folder_path)
    save_paths(PATH)
