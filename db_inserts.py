import json
import sqlite3
from datetime import datetime
from db_connect import get_db_connection

def insert_to_media_items_table(cursor, item):
    cursor.execute(''' 
        INSERT OR IGNORE INTO media_items (
            category,
            title,
            release_date,
            title_hash_key
        )
        VALUES (?, ?, ?, ?)
    ''', (
        item.get('category', None),
        item.get('title', None),
        item.get('release_date', None),
        item.get('title_hash_key', None)
    ))


def insert_to_media_metadata_table(cursor, item, media_item_id):
    cursor.execute('''
        INSERT OR IGNORE INTO media_metadata (
            media_item_id,
            season,
            episode,
            resolution, 
            extension, 
            path, 
            file_size,
            duration,
            audio_codec,
            video_codec,
            bitrate,
            frame_rate,
            width,
            height,
            aspect_ratio,    
            file_hash_key,
            key_frame
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
        media_item_id, 
        item.get('season', None),
        item.get('episode', None),
        item.get('resolution', None), 
        item.get('extension', None), 
        item.get('path', None), 
        item.get('file_size', None),
        item.get('duration', None),
        item.get('audio_codec', None),
        item.get('video_codec', None),
        item.get('bitrate', None),
        item.get('frame_rate', None),
        item.get('width', None),
        item.get('height', None),
        item.get('aspect_ratio', None),
        item.get('file_hash_key', None),
        item.get('key_frame', None)
    ))

def insert_to_tv_seasons_table(cursor, item, media_item_id):
    cursor.execute('''
        INSERT OR IGNORE INTO tv_seasons (
            media_item_id,
            season
        ) 
        VALUES (?, ?)''', (
        media_item_id, 
        item.get('season', None)
    ))

def insert_to_tv_episodes_table(cursor, item, media_item_id):
    cursor.execute('''
        INSERT OR IGNORE INTO tv_episodes (
            media_item_id,
            season,
            episode
        ) 
        VALUES (?, ?, ?)''', (
        media_item_id, 
        item.get('season', None),
        item.get('episode', None)
    ))



def insert_to_subtitles_table(cursor, item, media_metadata_id):
    subtitles = item.get('subtitles', [])

    if subtitles:
        for subtitle in subtitles:
            cursor.execute('''
                INSERT OR IGNORE INTO media_subtitles (
                    media_metadata_id,
                    subtitle_path
                ) 
                VALUES (?, ?)''', (
                int(media_metadata_id), 
                str(subtitle)
            ))



def api_insert_metadata_to_database(cursor, item_data, item_id, category, year):
    if item_data:
        cursor.execute('''
            UPDATE media_items
            SET 
                release_date = ?, 
                description = ?, 
                tagline = ?, 
                origin_country = ?, 
                spoken_languages = ?, 
                studio = ?, 
                production_countries = ?, 
                popularity = ?, 
                vote_average = ?, 
                vote_count = ?, 
                status = ?, 
                poster_path = ?,
                backdrop_path = ?, 
                tmdb_id = ?, 
                imdb_id = ?, 
                api_updated = ?
            WHERE id = ?  -- id is primary key
        ''', (
            item_data.get('release_date', year) if category == 'movie' else item_data.get('first_air_date', ''),
            item_data.get('overview', ''),
            item_data.get('tagline', ''),
            ', '.join(item_data.get('origin_country', [])),  # Ensure it's a comma-separated string
            ', '.join([lang.get('name', '') for lang in item_data.get('spoken_languages', [])]),  
            ', '.join([studio.get('name', '') for studio in item_data.get('production_companies', [])]),  
            ', '.join([country.get('name', '') for country in item_data.get('production_countries', [])]),  
            item_data.get('popularity', ''),
            round(item_data.get('vote_average', 0.0), 1),
            item_data.get('vote_count', ''),
            item_data.get('status', ''),
            item_data.get('poster_path', ''),
            item_data.get('backdrop_path', ''),
            item_data.get('id', ''),
            item_data.get('imdb_id', ''),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            item_id
        ))

        # If it's a movie, insert movie details
        if category == 'movie':
            cursor.execute('''
                INSERT INTO movie_details (
                    media_item_id, 
                    budget, 
                    revenue, 
                    duration
                )
                VALUES (?, ?, ?, ?)''', (
                item_id,
                "{:,}".format(int(item_data.get('budget', 0) or 0)),
                "{:,}".format(int(item_data.get('revenue', 0) or 0)),
                item_data.get('runtime', 0)
            ))

        # If it's a TV series, insert TV series details
        if category == 'tv':
            next_episode_air_date = item_data.get('next_episode_to_air', None)
            if next_episode_air_date:
                next_episode_air_date = next_episode_air_date.get('air_date', '')
            else:
                next_episode_air_date = ''
            cursor.execute('''
                INSERT OR IGNORE INTO tv_series_details (
                    media_item_id, 
                    created_by, 
                    first_air_date, 
                    last_air_date, 
                    next_episode_to_air, 
                    number_of_episodes, 
                    number_of_seasons, 
                    in_production
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
                item_id,
                json.dumps([creator['name'] for creator in item_data.get('created_by', [])]),  # Convert to JSON
                item_data.get('first_air_date', ''),
                item_data.get('last_air_date', ''),
                next_episode_air_date,
                item_data.get('number_of_episodes', 0),
                item_data.get('number_of_seasons', 0),
                int(item_data.get('in_production', False))
            ))
            # Process each season from API data
            for season in item_data['seasons']:
                season_number = season['season_number']

                # Check if the season already exists
                cursor.execute('''
                    SELECT id FROM tv_seasons WHERE media_item_id = ? AND season = ?
                ''', (item_id, season_number))
                
                existing_season = cursor.fetchone()

                if existing_season:
                    # Update existing season
                    cursor.execute('''
                        UPDATE tv_seasons
                        SET air_date = ?, episode_count = ?, tmdb_id = ?, season_name = ?, 
                            overview = ?, season_poster_path = ?, latest_episode_entry = datetime('now')
                        WHERE media_item_id = ? AND season = ?
                    ''', (
                        season['air_date'],
                        season['episode_count'],
                        season['id'],
                        season['name'],
                        season['overview'],
                        season['poster_path'],
                        item_id,
                        season_number
                    ))
        # Handle genres
        for genre in item_data.get('genres', []) or []:
            genre_name = genre.get('name', '')

            # Insert each genre into the genres table (if not already exists)
            cursor.execute('''INSERT OR IGNORE INTO genres (genre) VALUES (?)''', (genre_name,))

            # Get the genre_id for the genre
            result = cursor.execute('''SELECT id FROM genres WHERE genre = ?''', (genre_name,)).fetchone()

            if result:  # Ensure result is not None
                genre_id = result[0]
                cursor.execute('''INSERT OR IGNORE INTO media_genres (media_item_id, genre_id) VALUES (?, ?)''', (item_id, genre_id))
            else:
                print(f"[ tmdb.api warning ] Genre '{genre_name}' not found in database.")


def insert_movie(movie):
    conn = get_db_connection()
    cursor = conn.cursor()
    existing_item = cursor.execute("SELECT media_item_id FROM media_metadata WHERE file_hash_key = ?", (movie["file_hash_key"],)).fetchone()
    if existing_item:
        return

    existing_item = cursor.execute("SELECT id FROM media_items WHERE title_hash_key = ?", (movie["title_hash_key"],)).fetchone()
    if not existing_item:
        insert_to_media_items_table(cursor, movie)
        existing_item = cursor.lastrowid
    else:
        existing_item = existing_item[0]

    
    insert_to_media_metadata_table(cursor, movie, existing_item)

    metadata_table_id = cursor.lastrowid
    insert_to_subtitles_table(cursor, movie, metadata_table_id)

    conn.commit()
    conn.close() 



def insert_tv_series(serie):
    # serie input: [{'title': 'Gen V', 'season': 1, 'episode': 1, 'path': 'D:/Lib/series/Gen V/Season 01/gen v s01e01.mkv', ...}]
    conn = get_db_connection()
    cursor = conn.cursor()    
    existing_item = cursor.execute("SELECT media_item_id FROM media_metadata WHERE file_hash_key = ?", (serie["file_hash_key"],)).fetchone()
    if existing_item:
        return
    



    existing_item = cursor.execute("SELECT id FROM media_items WHERE title_hash_key = ?", (serie["title_hash_key"],)).fetchone()
    if not existing_item:
        insert_to_media_items_table(cursor, serie)
        existing_item = cursor.lastrowid
    else:
        existing_item = existing_item[0]

        
    insert_to_media_metadata_table(cursor, serie, existing_item)


    metadata_table_id = cursor.lastrowid
    insert_to_subtitles_table(cursor, serie, metadata_table_id)


    existing_season = cursor.execute("SELECT id FROM tv_seasons WHERE media_item_id = ? AND season = ?", (existing_item, serie["season"])).fetchone()
    if not existing_season:
        insert_to_tv_seasons_table(cursor, serie, existing_item)   
    


    existing_episode = cursor.execute("SELECT id FROM tv_episodes WHERE media_item_id = ? AND season = ? AND episode = ?", (existing_item, serie["season"], serie["episode"])).fetchone()
    if not existing_episode:
        insert_to_tv_episodes_table(cursor, serie, existing_item)

    conn.commit()
    conn.close()