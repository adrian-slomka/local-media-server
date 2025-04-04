
#'''========/// API's MOVIES and SERIES output: ///========'''
#   https://developer.themoviedb.org/reference

import os
import json
import time
import requests
from datetime import datetime, timedelta

from tmdb_request import api_request




def init_api(category, title, year = None, title_hash = None, api_updated = None, seasons_data = None):
    # category = must be a str of either "movie" or "tv"
    # title = must be a str "Dune: Part Two"
    # year (optional) must be YYYY int or str 
    # title_hash (optional) = must be a str                 >> unique name to save metadata backup with and later retrieve if needed
    # api_updated (optional) = must be '%Y-%m-%d %H:%M:%S'      >> check if data is recent, for example if less than "timedelta_value = 1" it will not request data that isnt older than a day
    timedelta_value = 1 # IN DAYS -- variable for is_recent()
    item_data = None
    start_time = time.time()


    if category == 'movie':
        # If api_updated return None (do nothing)
        if api_updated:
            return None

        # If api_updated is not provided, fetch data
        if not api_updated:
            if is_stored_locally(title_hash):
                item_data = get_local_data(title_hash)
                requested = False
            else:
                item_data = api_request(title, category, year)
                requested = True

    elif category == 'tv':
        # If api_updated is provided and is recent, return None (do nothing)
        if api_updated and series_recently_updated(seasons_data, timedelta_value):
            return None

        # If api_updated is not provided or not recent, fetch new data
        if not series_recently_updated(seasons_data, timedelta_value):
            if is_stored_locally(title_hash):
                item_data = get_local_data(title_hash)
                requested = False
            else:
                item_data = api_request(title, category, year)
                requested = True
            
     



    if not item_data:
        print(f"[ tmdb warning ] item_data for {title} is None, skipping...")
        return {}  # Return an empty dictionary if item_data is None

    item_data = standardize_genres(item_data)
   
    # If item_data has poster_path, try to download the image
    if item_data and item_data.get('poster_path'):
        try:
            download_image(item_data.get('poster_path'), 'poster')
        except Exception as e:
            print(f"[tmdb warning] Failed to download poster for {title}: {e}")

    if item_data and item_data.get('backdrop_path'):
        try:
            download_image(item_data.get('backdrop_path'), 'backdrop')
        except Exception as e:
            print(f"[tmdb warning] Failed to download backdrop poster for {title}: {e}")

    # Save metadata backup if item_data is available
    if item_data:
        try:
            save_metadata_backup(title, title_hash, item_data)
        except Exception as e:
            print(f'[ tmdb warning ] Failed to save metadata for {title} _ {e})')




    end_time = time.time()
    duration_movies = end_time - start_time
    print(f"[ tmdb ] {title} | Data processed in {duration_movies:.3f}s | New Request was made: {requested}")

    return item_data
  


def is_recent(when_updated, timedelta_value):
    if not when_updated:
        return False
    api_updated_date = datetime.strptime(when_updated, '%Y-%m-%d %H:%M:%S')
    if api_updated_date > datetime.now() - timedelta(days=timedelta_value):
        return True
    return False

def series_recently_updated(seasons_data, timedelta_value):
    if not seasons_data:
        return True 
    
    # latest season number
    most_recent_season = 0
    for season in seasons_data:
        if int(season['season']) > most_recent_season:
            most_recent_season = int(season['season'])

    _list_ = []
    for season in seasons_data:
        if not season['latest_episode_entry']:
           return False    # Update if there's None in season['latest_episode_entry']
        else:   # append when was the last time season updated with it's corresponding id
            _list_.append((int(season['season']), is_recent(season['latest_episode_entry'], timedelta_value)))   # is_recent() True if newest epsiode entry date not older timedelta_value (in days)

    # Return False only if it's the most recent / last season and was not updated within a timedelta_value
    for recent_entry in _list_:
        s_number, bool_value = recent_entry

        if s_number == most_recent_season and bool_value == False:
            return False
        
    return True

def is_stored_locally(title_hash):
    hash_filename = f"{title_hash}.json"
    # Get only the filenames from 'api_metadata/' directory
    for file in os.listdir('api_metadata/'):
        if file.split("_")[-1] == hash_filename:  # Extract last part and compare
            return True
        
    return False


def get_local_data(title_hash):
    hash_filename = f"{title_hash}.json"
    # Get only the filenames from 'api_metadata/' directory
    for file in os.listdir('api_metadata/'):
        if file.split("_")[-1] == hash_filename:  # Extract last part and compare
            with open(f"api_metadata/{file}", "r") as f:
                item_data = json.load(f)
                return item_data
        

def save_metadata_backup(title, title_hash, item_data):
    # Ensure the directory 'api_metadata' exists
    os.makedirs('api_metadata', exist_ok=True)
    filename = f'tmdb_{title.lower().replace(" ", "_")}_metadata_{title_hash}.json' 
    # Write metadata
    with open(f'api_metadata/{filename}', 'w') as file:
        json.dump(item_data, file)

            
def download_image(url, f_type):
    # url: "/3124shfgghff32314123.jpg"
    if f_type == 'poster':
        SAVE_FOLDER = "static/images/posters"
        image_urls = [
        "https://image.tmdb.org/t/p/w400/",         # 400x600px
        "https://image.tmdb.org/t/p/original/",     # Original size, px not specified
        ]

    elif f_type == 'backdrop':
        SAVE_FOLDER = "static/images/backdrops"
        image_urls = [
        "https://image.tmdb.org/t/p/original/",     # Original size, px not specified
        ]

    else:
        print(f'[ warning ] Could not extract image.')
        return


    # Ensure the folder exists
    os.makedirs(SAVE_FOLDER, exist_ok=True)

    

    for width in image_urls:
        file_width = width.split("/")[-2]
        url_path = width+url

        filename = os.path.join(SAVE_FOLDER, f"{file_width}_{os.path.basename(url)}")
        if os.path.exists(filename):
            continue

        response = requests.get(url_path, stream=True) 

        if response.status_code == 200:
            with open(filename, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
        else:
            print(f"[ tmdb warning ] Failed to download image: {url_path}")


def standardize_genres(item_data):
    """Standardizes genres while preserving the dictionary structure."""

    genre_map = {
        "Science Fiction": "Sci-Fi",
        "Sci-Fi & Fantasy": ["Sci-Fi", "Fantasy"],
        "Action & Adventure": ["Action", "Adventure"],
        "War & Politics": ["War", "Politics"],
        "Mystery & Thriller": ["Mystery", "Thriller"],
    }

    new_genres = []
    existing_ids = set()  # Avoid duplicate genres

    for genre in item_data.get("genres", []):
        name = genre["name"].strip()
        genre_id = genre["id"]

        if name in genre_map:
            mapped = genre_map[name]
            if isinstance(mapped, list):  # If it needs to be split into multiple
                for new_name in mapped:
                    if new_name not in existing_ids:  # Prevent duplicates
                        new_genres.append({"id": None, "name": new_name})  # Assign None for new IDs
                        existing_ids.add(new_name)
            else:
                if mapped not in existing_ids:
                    new_genres.append({"id": genre_id, "name": mapped})
                    existing_ids.add(mapped)
        else:
            if name not in existing_ids:
                new_genres.append(genre)
                existing_ids.add(name)

    item_data["genres"] = new_genres  # Replace the original genres

    return item_data

