import os
from math import ceil
from waitress import serve
from flask import Flask, request, render_template, send_from_directory,  redirect, url_for, jsonify


from load_data import MediaItem
from database_create import create_database
from directory_manager import create_settings, create_or_update_path
from watchdog_scanner import start_watchdog
from library_manager import library_manager







app = Flask(__name__)

def format_duration(minutes):
    """Converts minutes to hours and minutes format."""
    if minutes is None or minutes == "":
        return "N/A"
    try:
        minutes = int(minutes)  # Ensure it's an integer
        hours = minutes // 60
        remaining_minutes = minutes % 60

        if hours > 0 and remaining_minutes > 0:
            return f"{hours} hrs {remaining_minutes} min"
        elif hours > 0:
            return f"{hours} hrs"
        else:
            return f"{remaining_minutes} min"
    except ValueError:
        return "N/A"  # If the input isn't valid

# Register the filter so Jinja can use it in templates
app.jinja_env.filters['format_duration'] = format_duration








@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'4304.webp', mimetype='image/vnd.microsoft.icon')



@app.route('/')
@app.route('/index')
def index():
    try:
        # Limit the number of media items to 20
        media_items = MediaItem.load_media_with_limit(20)
        movies = MediaItem.load_media_with_limit(20, 'movie')
        series = MediaItem.load_media_with_limit(20, 'series')

    except Exception as e:
        media_items = []
        print(f"Failed to load data: {e}")

    return render_template('index.html', media_items=media_items, movies=movies, series=series)




@app.route('/new')
def recently_added_page():
    try:
        # Get the current page number from the query parameter, default to 1
        page = int(request.args.get('page', 1))

        # Limit the number of media items per page
        items_per_page = 20

        # Calculate the offset
        offset = (page - 1) * items_per_page

        # Fetch media items for the current page, limiting the results
        media_items = MediaItem.load_recently_added_page_with_limit_and_offset(items_per_page, offset)
        # Get the total count of media items to calculate the number of pages
        total_items = MediaItem.get_total_media_count()
        total_pages = (total_items // items_per_page) + (1 if total_items % items_per_page else 0)

    except Exception as e:
        media_items = []
        total_pages = 1  # Set at least one page if something fails
        print(f"Failed to load data: {e}")

    return render_template('recently_added_page.html', media_items=media_items, total_pages=total_pages, current_page=page)


@app.route('/movies')
def movies_page():
    try:
        # Get the current page number from the query parameter, default to 1
        page = int(request.args.get('page', 1))

        # Limit the number of media items per page
        items_per_page = 20

        # Calculate the offset
        offset = (page - 1) * items_per_page

        # Fetch media items for the current page, limiting the results
        media_items = MediaItem.load_movies_only_with_limit_and_offset(items_per_page, offset)
        # Get the total count of media items to calculate the number of pages
        total_items = MediaItem.get_total_media_count(category='movie')
        total_pages = (total_items // items_per_page) + (1 if total_items % items_per_page else 0)

    except Exception as e:
        media_items = []
        total_pages = 1  # Set at least one page if something fails
        print(f"Failed to load data: {e}")

    return render_template('movies_page.html', media_items=media_items, total_pages=total_pages, current_page=page)


@app.route('/series')
def series_page():
    try:
        # Get the current page number from the query parameter, default to 1
        page = int(request.args.get('page', 1))

        # Limit the number of media items per page
        items_per_page = 20

        # Calculate the offset
        offset = (page - 1) * items_per_page

        # Fetch media items for the current page, limiting the results
        media_items = MediaItem.load_series_only_with_limit_and_offset(items_per_page, offset)
        # Get the total count of media items to calculate the number of pages
        total_items = MediaItem.get_total_media_count(category='series')
        total_pages = (total_items // items_per_page) + (1 if total_items % items_per_page else 0)

    except Exception as e:
        media_items = []


        total_pages = 1  # Set at least one page if something fails
        print(f"Failed to load data: {e}")

    return render_template('series_page.html', media_items=media_items, total_pages=total_pages, current_page=page)



@app.route('/watchlist')
def watchlist():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        watchlist_items = cursor.execute('''SELECT media_item_id FROM user_profile WHERE watchlist = 1''').fetchall()
        conn.close()

        watchlist_ids = [item[0] for item in watchlist_items]
        ids_tuple = tuple(watchlist_ids)
        # Fetch media items for the current page, limiting the results
        media_items = MediaItem.get_watchlist(list(ids_tuple))
    except Exception as e:
        media_items = []
        print(f"Failed to load data: {e}")

    return render_template('watchlist_page.html', media_items=media_items)


@app.route('/<int:item_id>/<title>')
def details_page(item_id, title):

    try:    
        media_items = MediaItem.load_by_id(int(item_id))
        duration = MediaItem.calculate_average_duration(media_items.media_metadata)
    except Exception as e:
        media_items = []
        print(f"[ 10 ] Failed to load data: {e}")
    
    return render_template('item_page.html', media_items=media_items, item_id=item_id, title=title, duration=duration)


import tkinter as tk
from tkinter import filedialog

def show_file_dialog(category):
    """NOT IMPLEMENTED"""
    return None

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    folder_path = None  # Variable to store the selected folder path
    if request.method == 'POST':  # Check if the request is POST
        category = request.form.get('category')  # Get 'category' from the form
        
        # Open Window to choose path ++INCOMPLETE
        folder_path = show_file_dialog(category)    
        
        if folder_path:
            create_or_update_path(category, folder_path)
            return redirect(url_for('settings'))

        return render_template('settings.html')

    # Handle GET request (initial page load)
    return render_template('settings.html')




@app.route('/search', methods=['GET'])
def search_page():
    return render_template('search.html')



@app.route('/search/results', methods=['GET'])
def search_results():
    query = request.args.get('query', '')  # Get the 'query' parameter from the URL
    results_list = []

    if query:
        # Call the search method in the MediaItem model to search the database
        list = MediaItem.search(query)
        results_list = [item.to_dict() for item in list]
        
    # Return the results as JSON
    return jsonify(results=results_list)


from db_connect import get_db_connection

@app.route('/watch/v')
def watch():
    path = request.args.get('path')
    conn = get_db_connection()
    cursor = conn.cursor()
    item = cursor.execute('''SELECT * FROM media_metadata WHERE file_hash_key = ?''', (path,)).fetchone()
    
    conn.close()
    
    if item:
        # Assuming the 'path' column contains the full file path
        full_path = item['path']
        
        # Get the directory and file name separately
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        
        return send_from_directory(directory, filename)
    else:
        return "Item not found", 404

@app.route('/watch/s')
def subtitles():
    path = request.args.get('path')
    conn = get_db_connection()
    cursor = conn.cursor()
    item = cursor.execute('''SELECT * FROM media_metadata WHERE file_hash_key = ?''', (path,)).fetchone()
    subtitles = cursor.execute('''SELECT subtitle_path FROM media_subtitles WHERE media_metadata_id = ?''', (item['id'],)).fetchall()
    conn.close()

    if subtitles:
        directory = os.path.dirname(subtitles[0][0])
        subtitles = os.path.basename(subtitles[0][0])       
        return send_from_directory(directory, subtitles)
    else:
        return "Item not found", 404

@app.route('/watch')
def watch_page():
    path = request.args.get('path')
    conn = get_db_connection()
    cursor = conn.cursor()
    item = cursor.execute('''SELECT media_item_id, season, episode FROM media_metadata WHERE file_hash_key = ?''', (path,)).fetchone()
    title = cursor.execute('''SELECT title FROM media_items WHERE id = ?''', (item[0],)).fetchone()[0]
    conn.close()
    if item[1] and item[2]:
        title = f"{title} Season {item[1]} Episode {item[2]}"
    return render_template('watch.html', path=path, title=title)



# Route to submit a rating for an item
@app.route('/submit_rating', methods=['POST'])
def submit_rating():
    data = request.get_json()
    rating_value = data.get('rating')
    media_item_id = data.get('item_id')
    user_id = 1

    if rating_value and media_item_id:
        # Insert the rating into the ratings table
        conn = get_db_connection()
        cursor = conn.cursor()

        # Try to update the rating
        cursor.execute('''
            UPDATE user_profile
            SET rating = ?
            WHERE user_id = ? AND media_item_id = ?
        ''', (rating_value, user_id, media_item_id))

        # Check if any rows were updated
        if cursor.rowcount == 0:
            # If no row was updated, insert a new row with the rating
            cursor.execute('''
                INSERT INTO user_profile (user_id, media_item_id, rating)
                VALUES (?, ?, ?)
            ''', (user_id, media_item_id, rating_value))


        conn.commit()
        conn.close()

        return jsonify({"message": "Rating submitted successfully!"}), 200
    else:
        return jsonify({"message": "Invalid data."}), 400


@app.route('/get_rating/<int:item_id>', methods=['GET'])
def get_rating(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    avg_rating = cursor.execute("SELECT rating FROM user_profile WHERE media_item_id = ?", (item_id,)).fetchone()
    conn.close()

    if avg_rating is None:
        return jsonify({"message": "No ratings yet for this item."}), 404
    else:
        return jsonify({"item_id": item_id, "average_rating": avg_rating[0]}), 200


# Route to submit a rating for an item
@app.route('/submit_liked', methods=['POST'])
def submit_liked():
    data = request.get_json()
    liked_value = data.get('liked')
    media_item_id = data.get('item_id')
    user_id = 1

    if media_item_id:
        # Insert the rating into the ratings table
        conn = get_db_connection()
        cursor = conn.cursor()

        # Try to update the rating
        cursor.execute('''
            UPDATE user_profile
            SET watchlist = ?
            WHERE user_id = ? AND media_item_id = ?
        ''', (liked_value, user_id, media_item_id))

        # Check if any rows were updated
        if cursor.rowcount == 0:
            # If no row was updated, insert a new row with the rating
            cursor.execute('''
                INSERT INTO user_profile (user_id, media_item_id, watchlist)
                VALUES (?, ?, ?)
            ''', (user_id, media_item_id, liked_value))


        conn.commit()
        conn.close()

        return jsonify({"message": "Like submitted successfully!"}), 200
    else:
        return jsonify({"message": "Invalid data."}), 400


@app.route('/get_liked_status/<int:item_id>', methods=['GET'])
def get_liked_status(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    result = cursor.execute("SELECT watchlist FROM user_profile WHERE media_item_id = ?", (item_id,)).fetchone()
    conn.close()

    if result is None:
        return jsonify({"liked": 0}), 200  # Return 0 if the user hasn't liked the item
    else:
        return jsonify({"liked": result[0]}), 200


# Route to submit a watched status for an item
@app.route('/submit_watched', methods=['POST'])
def submit_watched():
    data = request.get_json()
    watched_value = data.get('watched')
    media_metadata_id = data.get('item_id')
    media_item_id = data.get('media_item_id')
    user_id = 1

    if media_metadata_id:
        # Insert the rating into the ratings table
        conn = get_db_connection()
        cursor = conn.cursor()

        # Try to update the rating
        cursor.execute('''
            UPDATE user_profile_items
            SET watched = ?
            WHERE user_id = ? AND media_metadata_id = ?
        ''', (watched_value, user_id, media_metadata_id))

        # Check if any rows were updated
        if cursor.rowcount == 0:
            # If no row was updated, insert a new row with the rating
            cursor.execute('''
                INSERT INTO user_profile_items (user_id, media_item_id, media_metadata_id, watched)
                VALUES (?, ?, ?, ?)
            ''', (user_id, media_item_id, media_metadata_id, watched_value))


        conn.commit()
        conn.close()

        return jsonify({"message": "Watched status submitted successfully!"}), 200
    else:
        return jsonify({"message": "Invalid data."}), 400
    

@app.route('/get_watched_status/<int:item_id>', methods=['GET'])
def get_watched_status(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    result = cursor.execute("SELECT media_metadata_id, watched FROM user_profile_items WHERE media_item_id = ?", (item_id,)).fetchall()
    conn.close()

    # If no results found, return an empty list
    if not result:
        return jsonify({"watched": [], "metadata_item_ids": []}), 200

    # Unpack the results into separate lists
    metadata_item_ids = [row[0] for row in result]
    watched_statuses = [row[1] for row in result]

    # Return the results as a JSON response
    return jsonify({"watched": watched_statuses, "metadata_item_ids": metadata_item_ids}), 200
    



if __name__ == "__main__":
    create_settings()
    create_database()
    
    library_manager()

    start_watchdog()

    # start_API_background_updates_thread() -- NOT YET IMPLEMENTED

    print("[ info ] Application is running...")
    serve(app, host="0.0.0.0", port=8000, threads=8)

    # app.run(host="0.0.0.0", port=8000, debug=True) -- for debug only