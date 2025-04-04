# '''========/// API's MOVIES and SERIES output: ///========'''
#   https://developer.themoviedb.org/reference


import os
import requests
import time 

from dotenv import load_dotenv
load_dotenv()



def api_request(title, category, year = None):
    time.sleep(0.2)  # 0.2s between the requests // Rate Limiting = They sit somewhere in the 50 requests per second range for TMDB API
    # title = must be a str "Dune: Part Two"
    # category = must be a str of either "movie" or "tv"
    # year (optional) must be YYYY int or str 

    tmdb_url = "https://api.themoviedb.org/3/"
    query_url = f"{tmdb_url}search/{category}?query={title}&include_adult=false&language=en-US&page=1" + (f"&year={year}" if year else "")
    
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {os.getenv('API_KEY')}"
    }


    try:
        # Make the initial request to TMDB API
        response = requests.get(query_url, headers=headers).json()

        # Check if there are any results
        if not response.get('results'):  # If 'results' is empty or doesn't exist
            print("[ tmdb.request warning ] No results found.")
            return

        # Get the top result's TMDB ID
        tmdb_id = response['results'][0]['id']

        # Construct the URL for more item details
        get_item_details_url = f"{tmdb_url}{category}/{tmdb_id}?language=en-US"
        
        # Fetch more details about the item
        item_data = requests.get(get_item_details_url, headers=headers).json()

        return item_data

    except requests.exceptions.RequestException as e:
        print(f"[ tmdb.request warning ] Error fetching data: {e}")
        return
    except KeyError as e:
        print(f"[ tmdb.request warning ] Missing expected key in response: {e}")
        return
    except IndexError as e:
        print(f"[ tmdb.request warning ] Error: List index out of range. No results found.")
        return









