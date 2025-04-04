import time
import threading
import os
import queue

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from directory_manager import load_paths
from library_manager import verify_library_integrity, remove_missing, check_entries_compatibility, get_hash_list_from_db, process_compatible
from extract_metadata import get_file_hash
from queue_tasks import add_to_queue

from threading import Timer

class MovieWatcher(FileSystemEventHandler):
    """Watchdog event handler to monitor movie and series folders."""

    def __init__(self):
        # Initialize the file queue for processing
        self.file_queue = queue.Queue()
        # Dictionary to keep track of files in each directory
        self.dir_files = {}

        # Load paths from the configuration
        self.paths = load_paths().get("libraries", {})
        self.series_paths = self.paths.get("series", [])
        self.movies_paths = self.paths.get("movies", [])

        # Create worker threads to process files in the queue
        self.worker_threads = []
        for _ in range(3):  # number of worker threads
            worker = threading.Thread(target=self.process_files_from_queue, daemon=True)
            self.worker_threads.append(worker)
            worker.start()


    def process_files_from_queue(self):
        """Worker thread that processes files from the queue."""
        while True:
            file_path, event = self.file_queue.get()  # Block until a file is added to the queue
            if file_path is None:
                break  # Exit if a None value is received
            self.process_new_file(file_path, event)
            self.file_queue.task_done()


    def _handle_file_creation(self, event):
        """Handle file creation event."""
        with open('watchdog_temp.txt', 'r') as f:
            lines = f.readlines()
        lines = [line.strip() for line in lines]
        lines = [os.path.normpath(line) for line in lines]
        normalized_path = os.path.normpath(event.src_path)

        # Check if the event's file path is already in the lines
        if normalized_path in lines:
            return True


        hash_list = get_hash_list_from_db()
        file = os.path.basename(event.src_path)
        root = os.path.dirname(event.src_path)

        try: 
            hash = get_file_hash(file, root)
        except PermissionError:
            return False    # Return False if there's a PermissionError 

        # Check if the event's file hash key is already in database
        if hash in hash_list:
            return True
        
        print(f"[+] New file detected: {event.src_path}")
        item = [(self._get_directory_type(event.src_path), file, root)]
        compatible_files, incompatible_files = check_entries_compatibility(item)

        if compatible_files:
            for file in compatible_files:
                # Process compatible files in a new thread to prevent blocking
                threading.Thread(target=process_compatible, args=(file,), daemon=True).start()

        if incompatible_files:
            for file in incompatible_files:
                # Add incompatible files to the queue for further processing
                threading.Thread(target=add_to_queue, args=(file,), daemon=True).start()

        return True
    
    def _handle_file_deletion(self, event):
        """Handle file deletion event."""
        with open('watchdog_temp.txt', 'r') as f:
            lines = f.readlines()
        lines = [line.strip() for line in lines]
        lines = [os.path.normpath(line) for line in lines]
        normalized_path = os.path.normpath(event.src_path)
        
        # Check if the event's file path is already in the lines
        if normalized_path in lines:
            return
        
        print(f"[-] File deleted: {event.src_path}")
        # Implement removal logic here
        new_entries_list, missing_entries_list = verify_library_integrity('movies', 'series')
        if missing_entries_list:
            remove_missing(missing_entries_list)

    def _get_directory_type(self, path):
        """Determine if the path is a 'series' or 'movies' directory."""
        if any(path.startswith(series_path) for series_path in self.series_paths):
            return "series"
        elif any(path.startswith(movie_path) for movie_path in self.movies_paths):
            return "movies"
        return "unknown"
    
    def wait_for_file(self, file_path, retries=10, wait_time=1):
        """Wait for the file to be available (not in use) before processing."""
        for _ in range(retries):
            if os.path.exists(file_path) and os.access(file_path, os.R_OK):
                return True
            time.sleep(wait_time)
        return False
    
    def process_new_file(self, file_path, event):
        """Process the new file"""
        if self.wait_for_file(file_path):
            # Retry _handle_file_creation only if a PermissionError occurs while getting file hash
            result = self._handle_file_creation(event)
            if result:  # File handled successfully
                pass
            else:
                print(f"Permission error: Could not access file hash for {file_path}. Retrying...")
                # Retry file handling if there was a PermissionError
                retries = 5  # Number of retries in case of PermissionError
                for _ in range(retries):
                    time.sleep(2)  # Wait for a moment before retrying
                    result = self._handle_file_creation(event)
                    if result:
                        break
                else:
                    print(f"Failed to access file after {retries} retries: {file_path}")
        else:
            print(f"File {file_path} is not ready for processing.")

    def on_created(self, event):
        """Handle file creation event."""
        directory_type = self._get_directory_type(event.src_path)
        if directory_type == "unknown":
            print(f"[!] Unknown directory type for file: {event.src_path}")
            return
        
        if event.src_path.endswith((".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm")):
            # Process the file (wait for it to be ready)
            self.file_queue.put((event.src_path, event))  # Add to queue for processing
            

    def on_deleted(self, event):
        """Handle file deletion event."""
        directory_type = self._get_directory_type(event.src_path)
        if directory_type == "unknown":
            print(f"[!] Unknown directory type for file: {event.src_path}")
            return
        
        if event.src_path.endswith((".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm")):
            self._handle_file_deletion(event)
        else:
            self._handle_file_deletion(event)





def start_monitoring():
    """Starts the watchdog observer to monitor folders, retrying if no paths exist."""
    while True:
        paths = load_paths().get("libraries", {})

        if not paths:
            print("[! error !] No paths to monitor! Retrying in 10 seconds...")
            time.sleep(10)
            continue  # Keep checking until paths are found

        # Start monitoring once paths exist
        event_handler = MovieWatcher()
        observer = Observer()

        for path_type, path_list in paths.items():
            for folder in path_list:
                observer.schedule(event_handler, folder, recursive=True)

        observer.start()
        print(f"[ watchdog ] Watching {list(paths.values())} for changes...")

        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\n[ watchdog ] Stopping observer...")
            observer.stop()

        return


def start_watchdog():
    """Start the database check in a background thread."""
    thread = threading.Thread(target=start_monitoring, daemon=True)
    thread.start()
