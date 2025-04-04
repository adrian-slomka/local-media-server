import time
import threading
from datetime import datetime

from db_connect import get_db_connection
from db_inserts import api_insert_metadata_to_database
from tmdb_processing import init_api


def API_database_update():
    """Function that checks for changes in the database every 30 minutes."""
    time.sleep(120)
    print(f"[ info ] {datetime.now()} Starting database update check...")

    # Start from row 0 and fetch rows 10 at a time
    offset = 0
    batch_size = 100

    conn = get_db_connection()
    cursor = conn.cursor()


    while True:
        # Connect to the database and check for updates

        rows = cursor.execute(f"SELECT id, category, title, release_date, title_hash_key, api_updated FROM media_items LIMIT {batch_size} OFFSET {offset}").fetchall()
        if not rows:
            break  # Exit if no rows are found

        print(f"[ info ] Processing batch from offset {offset}...")

        for row in rows:
            item_id = row["id"]
            category = row["category"]
            title = row["title"]
            year = row["release_date"]
            title_hash = row["title_hash_key"]
            api_updated = row["api_updated"]

            # Map the category to its string equivalent
            category = {
                "movie": "movie",
                "series": "tv"
            }.get(category, "unknown")  # Use 'unknown' if the value is not found
            
            
            item_data = init_api(category, title, year, title_hash, api_updated)

            if not item_data:
                continue

            try:
                api_insert_metadata_to_database(cursor, item_data, item_id, category, year)
                conn.commit()

            except Exception as e:
                print(f'[ tmdb warning ] Failed to insert to database for {title} _ {e}')        


            
            time.sleep(0.5)  # 1s between the requests // Rate Limiting = They sit somewhere in the 50 requests per second range for TMDB API
        # Move to the next batch of records
        offset += batch_size

    conn.close()

    # Schedule the next check
    print(f"[ tmdb info ] {datetime.now()} Waiting 12 hrs before the next database check...")
    threading.Timer(43200, API_database_update).start()

        

def start_API_background_updates_thread():
    """Start the database check in a background thread."""
    thread = threading.Thread(target=API_database_update, daemon=True)
    thread.start()
    return thread

# Only run when executed directly (NOT when imported)
if __name__ == "__main__":
    start_API_background_updates_thread()




