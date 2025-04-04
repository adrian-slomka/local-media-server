import os

from extract_metadata import *
from directory_manager import load_paths





def initialize_scanner(*categories):
    """Scans movies or series based on the given category."""
    PATH = load_paths()
    if not PATH:
        return
        #raise ValueError("No paths loaded. Check your configuration.")

    # Get paths for movies and series
    libraries = PATH.get("libraries", {})
    all_results = {}


    # Iterate over each category provided
    for category in categories:
        paths = libraries.get(category, [])  # Get paths for the specific category
        category_results = []

        # Scan each path for the current category
        for path in paths:
            results = scanner(path, category)
            if results:
                category_results.extend(results)

        # If there were results for this category, add them to the dictionary
        if category_results:
            all_results[category] = category_results
        else:
            all_results[category] = []

    return all_results





def scanner(path, category):
    """Scans a given directory for movies or series."""
    results = []
    count = 0
    for root, _, files in os.walk(path):
        for file in files:
            if not file.endswith((".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm")):
                continue
            
            count += 1
            results.append((file, os.path.normpath(root)))

    print(f'[ debug ] Found {count} files in "{path}"')
    return results


