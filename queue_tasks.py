import threading
import queue

from library_manager import process_incompatible
# Task queue to hold new file tasks
task_queue = queue.Queue()

def process_task():
    while True:
        file = task_queue.get()
        if file is None:
            break  # Stop processing when a sentinel value is received

        process_incompatible(file)

        task_queue.task_done()

# Worker thread to process tasks from the queue
worker_thread = threading.Thread(target=process_task, daemon=True)
worker_thread.start()

def add_to_queue(file):
    """Add files to the processing queue."""
    task_queue.put(file)

def stop_worker():
    """Stop the worker thread gracefully."""
    task_queue.put(None)  # Send sentinel value to stop the worker thread
    worker_thread.join()
