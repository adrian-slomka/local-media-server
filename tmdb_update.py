import time

from db_connect import get_db_connection
from db_inserts import api_insert_metadata_to_database
from tmdb_processing import init_api


def tmdb_api(hash_key):
    conn = get_db_connection()
    cursor = conn.cursor()

    item = cursor.execute("""
        SELECT mi.id, mi.category, mi.title, mi.release_date, mi.title_hash_key, mi.api_updated
        FROM media_items mi
        JOIN media_metadata mm ON mi.id = mm.media_item_id
        WHERE mm.file_hash_key = ?""", 
        (hash_key,)).fetchone()
    
    if not item:
        return


    item_id = item["id"]
    category = item["category"]
    title = item["title"]
    year = item["release_date"]
    title_hash = item["title_hash_key"]
    api_updated = item["api_updated"]

    # Map the category to its string equivalent
    category = {
        "movie": "movie",
        "series": "tv"
    }.get(category, None)
    
    if not category:
        return
    
    seasons_data = None
    if category == 'tv':
        seasons_data = cursor.execute("""
            SELECT s.media_item_id, s.season, s.latest_episode_entry
            FROM tv_seasons s
            JOIN media_items mm ON s.media_item_id = mm.id
            WHERE mm.id = ?""", 
            (item_id,)).fetchall()
        

    
    item_data = init_api(category, title, year, title_hash, api_updated, seasons_data)

    if not item_data:
        return

    try:
        api_insert_metadata_to_database(cursor, item_data, item_id, category, year)
        conn.commit()

    except Exception as e:
        print(f'[ tmdb warning ] Failed to insert to database for {title} _ {e}')        
    conn.close()

        




