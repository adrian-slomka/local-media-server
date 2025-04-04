import os
import time
import threading

from extract_metadata import *
from db_inserts import *
from transcode import *
from library_scanner import initialize_scanner
from db_connect import get_db_connection
from tmdb_update import tmdb_api

def get_hash_list_from_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        results = cursor.execute("SELECT file_hash_key FROM media_metadata").fetchall()
        hash_list = [row[0] for row in results]
        return hash_list
    except Exception as e:
        print(f"Error fetching hash list: {e}")
        return []
    finally:
        if conn:
            conn.close()


def verify_library_integrity(*categories):
    # files output:
    # {
    #     'movies': [(category, file, path), (category, file, path), ...],
    #     'series': [(category, file, path), (category, file, path), ...]
    # }

    start_time = time.time() # debug
    print(f"[ debug ] Verifying library integrity...")

    files = initialize_scanner(*categories)



    database_hash_list = get_hash_list_from_db()    # list of first 2 Mb hashed contents of a file


    local_hash_list = []
    new_entries_list = []
    missing_entries_list = []
    if files:
        for category, items in files.items():
            for item in items:
                file, root = item
                hash = get_file_hash(file, root)

                local_hash_list.append(hash)

                if hash in database_hash_list:
                    continue
                print(f'[ debug ] New entry -- {item}')
                new_entries_list.append((category, file, root))
    
        for hash in database_hash_list:
            if hash not in local_hash_list:
                missing_entries_list.append(hash)



    end_time = time.time()
    duration = end_time - start_time
    print(f"\n[ debug ] library scan completed in {duration:.3f}s")

    return new_entries_list, missing_entries_list







def check_entries_compatibility(files):
   
    compatible_files = []
    incompatible_files = []
    
    for file in files:
        category, file, root = file

        ffprobe_metadata = get_video_metadata(file, root)
        results = ffmpeg_video_metadata(ffprobe_metadata)

        video_codec = results.get('video_codec')
        audio_codec = results.get('audio_codec')
        extension = get_extension(file)

        if not (video_codec == 'h264' and audio_codec == 'aac' and extension == 'mp4'):
            incompatible_files.append((category, file, root))
            continue

        compatible_files.append((category, file, root))

    print(f'[ debug ] New compatible entries: {len(compatible_files)}')
    print(f'[ debug ] New incompatible entries: {len(incompatible_files)}')

    return compatible_files, incompatible_files



def remove_missing(missing_entries_list):
    conn = get_db_connection()
    cursor = conn.cursor()
        
    for item in missing_entries_list:
        cursor.execute("DELETE FROM media_metadata WHERE file_hash_key = ?", (item,))

    print(f"[ debug ] Missing entries removed: {len(missing_entries_list)}")

    conn.commit()
    conn.close()   



def process_compatible(item):
    start_time = time.time()

    category, file, root = item

    subtitles = get_all_subtitles(file, root)
    
    if category == 'movies':
        data = get_movie_metadata(file, root)
        if subtitles:
            data['subtitles'] = subtitles
        insert_movie(data)
        tmdb_api(data.get('file_hash_key'))



    if category == 'series':
        data = get_series_metadata(file, root)
        if subtitles:
            data['subtitles'] = subtitles
        insert_tv_series(data)
        tmdb_api(data.get('file_hash_key'))

    end_time = time.time()
    duration = end_time - start_time
    print(f'[ debug ] {file} -- Entry processed in {duration:.3f}s')


        


def process_incompatible(item):
    start_time = time.time()

    category, file, root = item

    subtitles = get_all_subtitles(file, root) # subs need to be extracted before transcoding

    file = transcode_to_mp4_264_aac(file, root)
    
    if category == 'movies':
        data = get_movie_metadata(file, root)
        if subtitles:
            data['subtitles'] = subtitles
        insert_movie(data)
        tmdb_api(data.get('file_hash_key'))

    if category == 'series':
        data = get_series_metadata(file, root)
        if subtitles:
            data['subtitles'] = subtitles
        insert_tv_series(data)
        tmdb_api(data.get('file_hash_key'))

    end_time = time.time()
    duration = end_time - start_time
    print(f'[ debug ] {file} -- Entry processed in {duration:.3f}s')



from queue_tasks import add_to_queue

def library_manager():
    new_entries_list, missing_entries_list = verify_library_integrity('movies', 'series')

    if missing_entries_list:
        remove_missing(missing_entries_list)

    compatible_files, incompatible_files = check_entries_compatibility(new_entries_list)


    if compatible_files:
        for file in compatible_files:
            process_compatible(file)

    if incompatible_files:
        for file in incompatible_files:
            add_to_queue(file)


    # threading.Thread(target=process_incompatible, args=(incompatible_files,), daemon=True).start()


 











 





