
import os
import sqlite3




def create():

    # Connect to SQLite database (creates file if it doesn’t exist)
    conn = sqlite3.connect("library.db")
    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON;")

    cursor = conn.cursor()

# TABLES
# TABLES
# TABLES

    # Table for Movies and TV Series Combined (media_items)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NULL,
            title TEXT NULL,
            release_date TEXT NULL,
            description TEXT NULL,
            tagline TEXT NULL,
            origin_country TEXT NULL,
            spoken_languages TEXT NULL,
            studio TEXT NULL,
            production_countries TEXT NULL,
            popularity REAL NULL,
            vote_average REAL NULL,
            vote_count INTEGER NULL,
            status TEXT NULL,
            poster_path TEXT NULL,
            backdrop_path TEXT NULL,
            title_hash_key TEXT NOT NULL UNIQUE,
            tmdb_id TEXT UNIQUE,
            imdb_id TEXT NULL,
            entry_updated TEXT DEFAULT (datetime('now')),
            api_updated TEXT NULL
        )
    ''')

    # Table for Movies specific (budget, revenue etc...)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movie_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_item_id INTEGER,
            budget INTEGER NULL,
            revenue INTEGER NULL,
            duration INTEGER NULL,
            FOREIGN KEY (media_item_id) REFERENCES media_items(id) ON DELETE CASCADE
        )
    ''')

    # Table for TV Series Details (additional info to specific serie)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tv_series_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_item_id INTEGER UNIQUE,
            created_by TEXT NULL, 
            first_air_date TEXT NULL,  
            last_air_date TEXT NULL,
            next_episode_to_air TEXT NULL,  
            number_of_episodes INTEGER NULL, 
            number_of_seasons INTEGER NULL,
            in_production BOOLEAN NULL,            
            FOREIGN KEY (media_item_id) REFERENCES media_items(id) ON DELETE CASCADE
        )
    ''')

    # Table for Seasons of the TV Series
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tv_seasons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_item_id INTEGER,  -- Foreign Key to tv_series_details
            season INTEGER,
            air_date TEXT NULL,
            episode_count INTEGER NULL,
            tmdb_id INTEGER NULL,
            season_name TEXT NULL,
            overview TEXT NULL,
            season_poster_path TEXT NULL,       
            latest_episode_entry TEXT NULL,     -- when's the last time episode was added to this series
            FOREIGN KEY (media_item_id) REFERENCES media_items(id) ON DELETE CASCADE
        )
    ''')

    # Table for Episodes (For TV Series only)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tv_episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_item_id INTEGER,
            season INTEGER,
            episode INTEGER,
            episode_title TEXT NULL,
            air_date TEXT NULL,
            duration TEXT NULL
        )
    ''')


    # Table for Metadata (For movies and episodes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_item_id INTEGER, 
            season INTEGER NULL,
            episode INTEGER NULL,
            resolution TEXT NULL,
            extension TEXT NULL,
            path TEXT UNIQUE,
            file_size TEXT NULL,
            duration TEXT NULL,
            audio_codec TEXT NULL,
            video_codec TEXT NULL,
            bitrate TEXT NULL,
            frame_rate TEXT NULL,
            width TEXT NULL,
            height TEXT NULL,
            aspect_ratio TEXT NULL,
            file_hash_key TEXT NOT NULL UNIQUE,
            key_frame TEXT,                   
            FOREIGN KEY (media_item_id) REFERENCES media_items(id) ON DELETE CASCADE
        )
    ''')

    # Table for Genres
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media_genres (
            media_item_id INTEGER,
            genre_id INTEGER,
            PRIMARY KEY (media_item_id, genre_id),
            FOREIGN KEY (media_item_id) REFERENCES media_items(id) ON DELETE CASCADE,
            FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
        )
    ''')

    # Table for Genres
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            genre TEXT UNIQUE
        )
    ''')

    # Table for Subtitles (For movies and episodes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media_subtitles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_metadata_id INTEGER,  -- References media_items
            subtitle_path TEXT,
            FOREIGN KEY (media_metadata_id) REFERENCES media_metadata(id) ON DELETE CASCADE
        )
    ''')

    # Table for User related data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, 
            media_item_id INTEGER NOT NULL,    -- References media_items id
            rating INTEGER,                    -- Rating given by the user (nullable)
            watchlist INTEGER,                 -- 1 for added to watchlist, 0 for not (nullable)
            FOREIGN KEY (media_item_id) REFERENCES media_items(id) -- Enforce foreign key constraint
        )
    ''')

    # Table for User related data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, 
            media_item_id INTEGER NOT NULL,         -- References media_items id
            media_metadata_id INTEGER NOT NULL,     -- References media_metadata id (nullable)
            watched INTEGER,                        -- 1 for watched, 0 for not watched (nullable)
            time_left REAL,                         -- Time remaining to finish (nullable)
            FOREIGN KEY (media_item_id) REFERENCES media_items(id), -- Enforce foreign key constraint
            FOREIGN KEY (media_metadata_id) REFERENCES media_metadata(id) -- Enforce foreign key constraint
        )
    ''')




    # Trigger to Delete Movie If No More Metadata Exists
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS delete_movie_if_no_metadata
        AFTER DELETE ON media_metadata
        FOR EACH ROW
        BEGIN
            DELETE FROM media_items
            WHERE id = OLD.media_item_id
            AND OLD.episode IS NULL -- Ensure it's a movie (episode is NULL for movies)
            AND NOT EXISTS (SELECT 1 FROM media_metadata WHERE media_item_id = OLD.media_item_id);
        END;
    ''')

    # Trigger to Delete TV Series if No More Metadata Exists for All Episodes
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS delete_tv_series_if_no_metadata
        AFTER DELETE ON media_metadata
        FOR EACH ROW
        BEGIN
            DELETE FROM media_items
            WHERE id = OLD.media_item_id
            AND OLD.episode IS NOT NULL -- Ensure it's a TV series episode (episode is NOT NULL)
            AND NOT EXISTS (
                SELECT 1 FROM media_metadata
                WHERE media_item_id = OLD.media_item_id
                AND season = OLD.season
                AND episode = OLD.episode
            )
            AND NOT EXISTS (
                SELECT 1 FROM media_metadata
                WHERE media_item_id = OLD.media_item_id
            );
        END;
    ''')
    
    # Trigger Auto-Update media_items.updated When Related Data Changes
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_media_item_timestamp
        AFTER INSERT ON media_metadata
        FOR EACH ROW
        BEGIN
            UPDATE media_items
            SET entry_updated = datetime('now')
            WHERE id = NEW.media_item_id;
        END;
    ''')
















    # JINDEX
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_items_title ON media_items (title);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_items_category ON media_items (category);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_items_release_date ON media_items (release_date);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_items_updated ON media_items (entry_updated);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_genres_genre_id ON media_genres (genre_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_metadata_path ON media_metadata (path);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_items_hashed_title ON media_items (title_hash_key);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_media_metadata_hashed_file ON media_metadata (file_hash_key);')
    





    conn.commit()
    conn.close()


def create_database():
    if os.path.exists("library.db"):
        print(f'[ info ] Database found.')   
    else:
        print(f'[ info ] Creating new database...')
        create()
