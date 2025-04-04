import sqlite3
from datetime import datetime




class MediaItem:
    def __init__(self, id=None, category=None, title=None, release_date=None, description=None, tagline=None, origin_country=None, 
                 spoken_languages=None, studio=None, production_countries=None, popularity=None, vote_average=None, vote_count=None, 
                 status=None, poster_path=None, backdrop_path=None, title_hash_key=None, tmdb_id=None, imdb_id=None, entry_updated=None, 
                 movie_details=None, tv_series_details=None, genres=None, tv_seasons=None, media_metadata=None, api_updated=None):
        self.id = id
        self.category = category
        self.title = title
        self.release_date = release_date
        self.description = description
        self.tagline = tagline
        self.origin_country = origin_country
        self.spoken_languages = spoken_languages
        self.studio = studio
        self.production_countries = production_countries
        self.popularity = popularity
        self.vote_average = vote_average
        self.vote_count = vote_count
        self.status = status
        self.poster_path = poster_path
        self.backdrop_path = backdrop_path
        self.title_hash = title_hash_key
        self.tmdb_id = tmdb_id
        self.imdb_id = imdb_id
        self.entry_updated = entry_updated
        self.movie_details = movie_details or {}
        self.tv_series_details = tv_series_details or {}
        self.genres = genres or []
        self.tv_seasons = tv_seasons or []
        self.media_metadata = media_metadata or []
        self.api_updated = api_updated



    @staticmethod
    def get_db_connection():
        conn = sqlite3.connect('library.db')
        conn.row_factory = sqlite3.Row  # Enables column access by name
        return conn


    @classmethod
    def load_by_id(cls, media_id):
        """Load a single media item by its ID, including connected genres, movie or TV details"""
        try:
            with cls.get_db_connection() as conn:
                # Query for the main media item
                media_item_data = conn.execute('''
                    SELECT * 
                    FROM media_items 
                    WHERE id = ?''', (media_id,)).fetchone()

                if media_item_data is None:
                    print(f"[ debug ] No media item found with ID: {media_id}")
                    return None

                print(f"[ debug ] Media item found: {media_item_data['title']}")

                # Movie details (if category is movie)
                movie_details = None
                if media_item_data['category'] == "movie":
                    movie_details = conn.execute('''
                        SELECT * 
                        FROM movie_details 
                        WHERE media_item_id = ?''', (media_id,)).fetchone()

                # TV series details (if category is series)
                tv_series_details = None
                if media_item_data['category'] == "series":
                    tv_series_details = conn.execute('''
                        SELECT * 
                        FROM tv_series_details 
                        WHERE media_item_id = ?''', (media_id,)).fetchone()

                # Fetch associated genres
                genres_data = conn.execute('''
                    SELECT g.genre 
                    FROM media_genres mg
                    JOIN genres g ON mg.genre_id = g.id
                    WHERE mg.media_item_id = ?''', (media_id,)).fetchall()

                genres = [genre['genre'] for genre in genres_data]

                # Fetch TV seasons (if it's a TV series)
                tv_seasons = []
                if media_item_data['category'] == 'series':
                    seasons_data = conn.execute('''
                        SELECT * 
                        FROM tv_seasons 
                        WHERE media_item_id = ?''', (media_id,)).fetchall()

                    for season in seasons_data:
                        tv_seasons.append({
                            'season': season['season'],
                            'air_date': season['air_date'],
                            'episode_count': season['episode_count'],
                            'season_name': season['season_name'],
                            'overview': season['overview'],
                            'season_poster_path': season['season_poster_path'],
                            'latest_episode_entry': season['latest_episode_entry']
                        })

                # Fetch media metadata (both for movies and episodes)
                media_metadata = []
                metadata_data = conn.execute('''
                    SELECT * 
                    FROM media_metadata 
                    WHERE media_item_id = ?''', (media_id,)).fetchall()

                for metadata in metadata_data:
                    media_metadata.append({
                        'id': metadata['id'],
                        'media_item_id': metadata['media_item_id'],
                        'season': metadata['season'],
                        'episode': metadata['episode'],
                        'resolution': metadata['resolution'],
                        'extension': metadata['extension'],
                        'path': metadata['path'],
                        'file_size': metadata['file_size'],
                        'duration': metadata['duration'],
                        'audio_codec': metadata['audio_codec'],
                        'video_codec': metadata['video_codec'],
                        'bitrate': metadata['bitrate'],
                        'frame_rate': metadata['frame_rate'],
                        'width': metadata['width'],
                        'height': metadata['height'],
                        'aspect_ratio': metadata['aspect_ratio'],
                        'file_hash_key': metadata['file_hash_key'],
                        'key_frame': metadata['key_frame']
                    })

                return cls(
                    id=media_item_data['id'],
                    category=media_item_data['category'],
                    title=media_item_data['title'],
                    release_date=media_item_data['release_date'],
                    description=media_item_data['description'],
                    tagline=media_item_data['tagline'],
                    origin_country=media_item_data['origin_country'],
                    spoken_languages=media_item_data['spoken_languages'],
                    studio=media_item_data['studio'],
                    production_countries=media_item_data['production_countries'],
                    popularity=media_item_data['popularity'],
                    vote_average=media_item_data['vote_average'],
                    vote_count=media_item_data['vote_count'],
                    status=media_item_data['status'],
                    poster_path=media_item_data['poster_path'],
                    backdrop_path=media_item_data['backdrop_path'],
                    title_hash_key=media_item_data['title_hash_key'],
                    tmdb_id=media_item_data['tmdb_id'],
                    imdb_id=media_item_data['imdb_id'],
                    entry_updated=media_item_data['entry_updated'],
                    movie_details=movie_details or {},
                    tv_series_details=tv_series_details or {},
                    genres=genres or [],
                    tv_seasons=sorted(tv_seasons or [], key=lambda x: x['season']),  # Sort by 'season' before passing
                    media_metadata=media_metadata or []
                )

        except sqlite3.DatabaseError as e:
            print(f"Error while querying database: {e}")
            return None     



    @classmethod
    def get_watchlist(cls, watchlist_ids):
        conn = cls.get_db_connection()
        
        if watchlist_ids:
            # Create a tuple of the same length as the number of watchlist_ids, with placeholders
            placeholders = ', '.join('?' for _ in watchlist_ids)

            # Modify the SQL query to include the placeholders
            query = f'''SELECT id, category, title, release_date, poster_path, entry_updated 
                        FROM media_items 
                        WHERE id IN ({placeholders}) 
                        ORDER BY entry_updated DESC'''
            
            # Execute the query, passing the watchlist_ids as arguments
            media_items = conn.execute(query, watchlist_ids).fetchall()
        else:
            media_items = []

        conn.close()

        items = []
        for item in media_items:
            media_item = cls(**dict(item))    
            items.append(media_item)    
        # Return the count (the result is a tuple, so we extract the first element)
        return items

    @classmethod
    def get_total_media_count(cls, category=None):
        conn = cls.get_db_connection()
        
        if category:
            # If category is provided, filter by category
            query = 'SELECT COUNT(*) FROM media_items WHERE category = ?'
            result = conn.execute(query, (category,)).fetchone()
        else:
            # If no category is provided, count all media items
            query = 'SELECT COUNT(*) FROM media_items'
            result = conn.execute(query).fetchone()
        
        conn.close()
        
        # Return the count (the result is a tuple, so we extract the first element)
        return result[0] if result else 0

    @classmethod
    def load_media_with_limit(cls, limit, category=None):
        """Fetch a limited set of media items, up to a specified limit."""
        conn = cls.get_db_connection()
        if category:
            media_items = conn.execute('SELECT id, category, title, release_date, poster_path, entry_updated FROM media_items WHERE category = ? ORDER BY entry_updated DESC LIMIT ?', (category, limit,)).fetchall()
        else:
            media_items = conn.execute('SELECT id, category, title, release_date, poster_path, entry_updated FROM media_items ORDER BY entry_updated DESC LIMIT ?', (limit,)).fetchall()
        

        items = []

        for item in media_items:
            media_item = cls(**dict(item))


            # Get genres for this media item (joining media_genres and genres)
            genres_data = conn.execute('''
                SELECT g.genre 
                FROM media_genres mg
                JOIN genres g ON mg.genre_id = g.id
                WHERE mg.media_item_id = ?''', (media_item.id,)).fetchall()
            genres = [genre['genre'] for genre in genres_data]
            media_item.genres = genres


            items.append(media_item)

        conn.close()
        return items

    @classmethod
    def load_recently_added_page_with_limit_and_offset(cls, limit, offset):
        conn = cls.get_db_connection()

        # Modified SQL query to include both LIMIT and OFFSET
        media_items = conn.execute(
            'SELECT id, category, title, release_date, description, poster_path, entry_updated '
            'FROM media_items ORDER BY entry_updated DESC LIMIT ? OFFSET ?',
            (limit, offset)
        ).fetchall()

        items = []

        for item in media_items:
            media_item = cls(**dict(item))


            # Get genres for this media item (joining media_genres and genres)
            genres_data = conn.execute('''
                SELECT g.genre 
                FROM media_genres mg
                JOIN genres g ON mg.genre_id = g.id
                WHERE mg.media_item_id = ?''', (media_item.id,)).fetchall()
            genres = [genre['genre'] for genre in genres_data]
            media_item.genres = genres


            items.append(media_item)        
        conn.close()

        # Convert to list of Media objects
        return items

    @classmethod
    def load_movies_only_with_limit_and_offset(cls, limit, offset):
        conn = cls.get_db_connection()

        # Modified SQL query to include both LIMIT and OFFSET
        media_items = conn.execute(
            'SELECT id, category, title, release_date, description, poster_path, entry_updated '
            'FROM media_items WHERE category = "movie" ORDER BY title DESC LIMIT ? OFFSET ?',
            (limit, offset)
        ).fetchall()

        items = []

        for item in media_items:
            media_item = cls(**dict(item))


            # Get genres for this media item (joining media_genres and genres)
            genres_data = conn.execute('''
                SELECT g.genre 
                FROM media_genres mg
                JOIN genres g ON mg.genre_id = g.id
                WHERE mg.media_item_id = ?''', (media_item.id,)).fetchall()
            genres = [genre['genre'] for genre in genres_data]
            media_item.genres = genres


            items.append(media_item)        
        conn.close()

        # Convert to list of Media objects
        return items

    @classmethod
    def load_series_only_with_limit_and_offset(cls, limit, offset):
        conn = cls.get_db_connection()

        # Modified SQL query to include both LIMIT and OFFSET
        media_items = conn.execute(
            'SELECT id, category, title, release_date, description, poster_path, entry_updated '
            'FROM media_items WHERE category = "series" ORDER BY title DESC LIMIT ? OFFSET ?',
            (limit, offset)
        ).fetchall()

        items = []

        for item in media_items:
            media_item = cls(**dict(item))


            # Get genres for this media item (joining media_genres and genres)
            genres_data = conn.execute('''
                SELECT g.genre 
                FROM media_genres mg
                JOIN genres g ON mg.genre_id = g.id
                WHERE mg.media_item_id = ?''', (media_item.id,)).fetchall()
            genres = [genre['genre'] for genre in genres_data]
            media_item.genres = genres


            items.append(media_item)        
        conn.close()

        # Convert to list of Media objects
        return items
    
    
    @classmethod
    def sort_media(cls, media_items, sort_type):
        """Sort the media items by sort_type: 'recent', 'oldest', or 'alphabetical'."""
        
        # Helper function to convert the 'entry_updated' string to datetime
        def parse_datetime(item):
            return datetime.strptime(item.entry_updated, "%Y-%m-%d %H:%M:%S")
        
        if sort_type == "recent":
            return sorted(media_items, key=lambda item: parse_datetime(item), reverse=True)
        
        elif sort_type == "oldest":
            return sorted(media_items, key=lambda item: parse_datetime(item), reverse=False)
        
        elif sort_type == "alphabetical":
            return sorted(media_items, key=lambda item: item.title.lower())
        
        # If no valid sort_type, return the list as is
        return media_items
    
    @classmethod
    def calculate_average_duration(cls, metadata):
        total_minutes = 0
        total_items = 0
        

        for item in metadata:
            # Extract the duration and split it into hours and minutes
            duration = item.get('duration', '')
            if duration:
                parts = duration.split(":")
                hours = int(parts[0])
                minutes = int(parts[1])
                total_minutes += (hours * 60 + minutes)
                total_items += 1

        # Calculate average if there are items
        if total_items > 0:
            average_minutes = total_minutes / total_items
            avg_hours = average_minutes // 60
            avg_remaining_minutes = average_minutes % 60
            return f"{int(avg_hours)}hr {int(avg_remaining_minutes)}min" if avg_hours > 0 else f"{int(avg_remaining_minutes)}min"

    @classmethod
    def search(cls, input_str):
        conn = cls.get_db_connection()
        cursor = conn.cursor()
        
        items = cursor.execute("SELECT * FROM media_items WHERE title LIKE ?", ('%' + input_str + '%',)).fetchall()
        

        items_list = []

        for item in items:
            media_item = cls(**dict(item))


            # Get genres for this media item (joining media_genres and genres)
            genres_data = conn.execute('''
                SELECT g.genre 
                FROM media_genres mg
                JOIN genres g ON mg.genre_id = g.id
                WHERE mg.media_item_id = ?''', (media_item.id,)).fetchall()
            genres = [genre['genre'] for genre in genres_data]
            media_item.genres = genres


            items_list.append(media_item)
        conn.close()

        return items_list
    

    def to_dict(self):
        # Convert object attributes into a dictionary
        return {
            'id': self.id,
            'title': self.title,
            'poster_path': self.poster_path,
            'category': self.category,
            'release_date': self.release_date,
            'genres': self.genres
        }