import re
import os
import time
import hashlib
import subprocess
import json
from datetime import datetime

def time_to_seconds(time_str):
    hours, minutes, seconds = map(int, time_str.split(':'))
    return hours * 3600 + minutes * 60 + seconds

def ffmpeg_key_frame(file, root, hash_key, duration):
    ffmpeg_path = os.path.join(os.getcwd(), 'ffmpeg.exe') 
    video_path = os.path.join(root, file).replace("\\", "/")

    SAVE_FOLDER = "static/images/keyFrames/"
    output_name = f'keyframe_{hash_key}.jpg'
    output_path = os.path.join(SAVE_FOLDER, output_name)

    if os.path.exists(output_path):
        return output_name

    # Check if ffprobe binary exists
    if not os.path.exists(ffmpeg_path):
        raise FileNotFoundError("ffmpeg binary not found. Please ensure ffmpeg is bundled with the application.")
    
    # Ensure the folder exists
    os.makedirs(SAVE_FOLDER, exist_ok=True)

    if not duration:
        return None
    
    duration_seconds = time_to_seconds(duration)
    offset_seconds = duration_seconds * 1/11
    
    # Convert the offset back to HH:MM:SS format
    hours = offset_seconds // 3600
    minutes = (offset_seconds % 3600) // 60
    seconds = int(offset_seconds % 60)
    offset_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    

    cmd = [
        ffmpeg_path,
        '-ss', offset_time, 
        '-i', video_path,
        '-frames:v', '1',
        '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease', 
        output_path
    ]
    
    subprocess.run(
        cmd, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        encoding='utf-8', errors='replace'
    )

    if output_name:
        return output_name
    else:
        return None    

def get_movie_metadata(file, root):
    # file output: Example.Media.2024.1080p.WEBRip.1400MB.DD5.1.x264-GalaxyRG.mp4
    # root output: D:/Lib/movies\Example Media\
    # media_file_path output: D:/Lib/movies/Example Media/Example.Media.2024.1080p.WEBRip.1400MB.DD5.1.x264-GalaxyRG.mp4 

    ffprobe_metadata = get_video_metadata(file, root)
    results = ffmpeg_video_metadata(ffprobe_metadata)

    file_hash_key = get_file_hash(file, root)

    movie_entry = []
    # Now create the movie_entry dictionary with the added metadata
    movie_entry = {
        'category': 'movie',
        'title': get_title(file),
        'title_hash_key': get_title_hash(file, 'movie'),
        'release_date': get_release_date(file, root),
        'extension': get_extension(file),
        'path': get_path(file, root),
        'file_size': get_size(file, root),
        'file_hash_key': file_hash_key,
        # video_metadata
        'resolution': results.get('resolution'),
        'duration': results.get('duration'),
        'audio_codec': results.get('audio_codec'),
        'video_codec': results.get('video_codec'),
        'bitrate': results.get('bitrate'),
        'frame_rate': results.get('frame_rate'),
        'width': results.get('width'),
        'height': results.get('height'),
        'aspect_ratio': results.get('aspect_ratio'),
        'key_frame': ffmpeg_key_frame(file, root, file_hash_key, results.get('duration'))
    }


    return movie_entry


def get_series_metadata(file, root):
    # file output: Example.SERIES.2024.S1E02.1080p.WEBRip.1400MB.DD5.1.x264-GalaxyRG.mp4
    # root output: D:/Lib/movies\Example Media\
    # media_file_path output: D:/Lib/series/Example Media/Example.SERIES.2024.S1E02.1080p.WEBRip.1400MB.DD5.1.x264-GalaxyRG.mp4
    media_file_root_path = os.path.join(root, file).replace("\\", "/") 
    
    ffprobe_metadata = get_video_metadata(file, root)
    results = ffmpeg_video_metadata(ffprobe_metadata)


    series_metadata = []
    
    # series_title, season, episode = get_series_info(file)  # output: str The Simpsons, int 1, int 20

    series_title = get_series_title(file, root)
    season = get_series_season(file)
    episode = get_series_episode(file)




    file_hash_key = get_file_hash(file, root)

    # Find or create the series entry
    series_entry = next((s for s in series_metadata if s["title"] == series_title), None)

    if not series_entry:
        series_entry = {
            'category': 'series',
            'title': series_title,
            'season': season,
            'episode': episode,
            'title_hash_key': get_title_hash(series_title, 'series'), 
            'release_date': get_release_date(file, root),
            'extension': get_extension(file),
            'path': get_path(file, root),
            'file_size': get_size(file, root),
            'file_hash_key': file_hash_key,
            # video_metadata
            'resolution': results.get('resolution'),
            'duration': results.get('duration'),
            'audio_codec': results.get('audio_codec'),
            'video_codec': results.get('video_codec'),
            'bitrate': results.get('bitrate'),
            'frame_rate': results.get('frame_rate'),
            'width': results.get('width'),
            'height': results.get('height'),
            'aspect_ratio': results.get('aspect_ratio'),
            'key_frame': ffmpeg_key_frame(file, root, file_hash_key, results.get('duration'))
        }

        series_metadata.append(series_entry)
    else:
        # If the series already exists, update the existing entry with new season/episode data
        series_entry['season'] = season
        series_entry['episode'] = episode
        series_entry['path'] = media_file_root_path
        
    return series_metadata[0] if series_metadata else {}

def get_series_title(file: str, root: str) -> str:
    pattern = r'^(?P<title>.+?)\.*(([sS])(\d{1,3})([eE])(\d{1,3})|\b\d{4}\b|\d{3,4}p)'  # Match anything till finds least one of: S01E01 or year or 2160p or ## extension |mp4|mkv|avi|mov|flv|wmv|webm)
    file = file.replace("(", "").replace(")", "").replace(".", " ").replace('_', ' ').replace("-", "")
    file = re.sub(r'\s+', ' ', file).strip()  # Replaces multiple spaces with a single space

    # Extract series title
    series_title = re.match(pattern, file)
    if series_title:
        series_title = series_title.group('title').strip().title()
        return series_title
    
    if not series_title:
        root = os.path.normpath(root)
        parts = root.split(os.sep)

        title = None
        # # If the path ends with a directory (e.g., "D:/Lib/series/"), return nothing
        # if len(parts) == 3:  # Meaning it's "D:/Lib/series/"
        #     pass
        
        # If the path contains a subdirectory for the series, return that
        if len(parts) == 4:  # "D:/Lib/series/Legend of The Galactic Heroes/"
            title = parts[-1]
        
        # If there's a season folder, return just the series name
        if len(parts) == 5:  # "D:/Lib/series/Legend of The Galactic Heroes/s01"
            title = parts[-2]

        if title:
            pattern_special = r'(.+?)\.*([sS]eason|[sS]\d{1,3}|\b\d{4}\b|\d{3,4}p|$)'
            title = title.replace("(", "").replace(")", "").replace(".", " ").replace('_', ' ').replace("-", "")
            title = re.sub(r'\s+', ' ', title).strip()

            series_title = re.match(pattern_special, title)
            if series_title:
                series_title = series_title.group(1).strip().title()
                return series_title
            
    return 'Unknown'

def get_series_season(file: str) -> int:
    pattern = r'([sS])(?P<season>\d{1,3})'    # Match: S01
    
    series_season = re.search(pattern, file)
    if series_season:
        season = int(series_season.group('season'))
        return season
    return 999

def get_series_episode(file: str) -> int:
    pattern = r'(?:[sS]\d{1,3}[eE]|[eE]|part|episode)\s?(?P<episode>\d{1,3})'

    series_episode = re.search(pattern, file.lower())
    if series_episode:
        episode = int(series_episode.group('episode'))
        return episode
    
    if not series_episode:
        pattern_special = r'(?P<episode>\d{1,3})'
        name = os.path.splitext(file)[0]

        series_episode = re.search(pattern_special, name)
        episode = int(series_episode.group('episode'))
        return episode
    
    return 999

def get_series_episode_title(file: str) -> str:
    pattern = r'(?:[sS]\d{1,3}[eE]\d{1,3}(?:\s+[eE]\d{1,3})?|part\s\d{1,3}|episode\s\d{1,3})(?P<title>.*?)(?=\s*(?:2160|1080|720|repack|WEBRip|mp4|mkv|avi|mov|flv|wmv|webm))'
    file = file.replace("(", "").replace(")", "").replace(".", " ").replace('_', ' ').replace("-", "")
    file = re.sub(r'\s+', ' ', file).strip()  # Replaces multiple spaces with a single space

    series_episode = re.search(pattern, file.lower())
    if series_episode:
        episode_title = str(series_episode.group('title').strip().title().replace("'S", "'s"))
        return episode_title
    return 'Unknown'

def get_title(file):
    # file output: Example.Media.2024.1080p.WEBRip.1400MB.DD5.1.x264-GalaxyRG.mp4
    pattern_title = r'^(?P<title>.+?)\.*(\b\d{4}\b|\d{3,4}p|mp4|mkv|avi|mov|flv|wmv|webm)'
    
    file = file.replace("(", "").replace(")", "").replace(".", " ").replace('_', ' ')

    # Collapse multiple spaces into one
    file = re.sub(r'\s+', ' ', file).strip()  # Replaces multiple spaces with a single space

    file_title = re.match(pattern_title, file)   # Matches with pattern
    if file_title:   # If no match instead of processing None, return Unknown
        
        file_title = file_title.group('title').strip()
     
        return file_title
    return 'Unknown'


def get_title_hash(file, media_type):
    # file = Avengers Endgame
    # media_type = movie or series
    unique_title = media_type + file
    hash_func = hashlib.md5()
    hash_func.update(unique_title.encode('utf-8'))

    return hash_func.hexdigest()


def get_release_date(file, root):
    pattern = r'(?P<year>\b\d{4}\b)'
    year_match = re.search(pattern, file)
    if year_match:
        return year_match.group('year')
    
    if not year_match:
        year_match = re.search(pattern, root)
        if year_match:
            return year_match.group('year')
        return None


def get_resolution(file):
    pattern = r'(?P<res>\d{3,4}p)'
    res_match = re.search(pattern, file)
    if res_match:
        return res_match.group('res')
    return None


def get_extension(file):
    extension = os.path.splitext(file)[1].replace(".","")
    if extension:
        return extension
    return None


def get_path(file, root):
    full_path = os.path.join(root, file).replace("\\", "/") 
    full_path = full_path.replace("\\", "/")
    if full_path:
        return full_path
    return None


def get_size(file, root):
    full_path = os.path.join(root, file).replace("\\", "/") 
    size_in_bytes = os.path.getsize(full_path)
    
    if size_in_bytes is not None:
        # Convert bytes to MB (1024^2 bytes in 1MB) or GB (1024^3 bytes in 1GB)
        size_in_mb = size_in_bytes / (1024 * 1024)  # Convert to MB
        size_in_gb = size_in_bytes / (1024 * 1024 * 1024)  # Convert to GB
        
        # Return size in MB if it's smaller than 1 GB, otherwise in GB
        if size_in_gb < 1:
            return f"{size_in_mb:.2f} MB"
        else:
            return f"{size_in_gb:.2f} GB"
    
    return None


def get_file_hash(file, root, portion_size=2 * 1024 * 1024):
    full_path = os.path.join(root, file).replace("\\", "/") 
    """
    Returns the MD5 hash of a file based on its file title, path, and a portion of its contents.

    :param portion_size: The amount of the file to hash
    :return: MD5 hash of the file and portion of the contents
    """
    hash_func = hashlib.md5()
    #hash_func.update(path.encode('utf-8'))

    with open(full_path, 'rb') as f:
        chunk = f.read(portion_size)
        hash_func.update(chunk)

    return hash_func.hexdigest()


def get_series_info(file):
    # possible inputs: 
    # Example.Series.(2024).S01E01.1080p.WEBRip.1400MB.DD5.1.x264-GalaxyRG.mp4
    # Example Series (2024) S01E01.mp4
    # Example Series S01E01.mp4
    pattern_series_title = r'^(?P<title>.+?)\.*(([sS])(\d{1,3})([eE])(\d{1,3})|\b\d{4}\b|\d{3,4}p|mp4|mkv|avi|mov|flv|wmv|webm)'  # Match anything till finds least one of: S01E01 or year or 2160p or extension
    pattern_season_episode = r'(?P<full>([sS])(?P<season>\d{1,3})([eE])(?P<episode>\d{1,3}))'    # Match anything till finds: S01E01

    file = file.replace("(", "").replace(")", "").replace(".", " ").replace('_', ' ').replace("-", "")
    
    # Collapse multiple spaces into one
    file = re.sub(r'\s+', ' ', file).strip()  # Replaces multiple spaces with a single space

    # Extract series title
    series_title = re.match(pattern_series_title, file)
    if series_title:
        series_title = series_title.group('title').strip().title()

    # Extract season and episode numbers
    season_episode_match = re.search(pattern_season_episode, file)
    if season_episode_match:
        season = int(season_episode_match.group('season'))
        episode = int(season_episode_match.group('episode'))
        return (series_title, season, episode)
    
    fallback_pattern = r"(?P<first_word>\w+)"  # Matches a single word (a sequence of alphanumeric characters and underscores)
    fallback_name = re.search(fallback_pattern, file)
    fallback_name = fallback_name.group('first_word').strip().title()
    # If no match found, return a default value
    return fallback_name, 999, int(time.time())  # title, season, ep










def convert_srt_to_vtt(srt_file_path, vtt_file_path):
    """Converts an SRT file to a VTT file and deletes the original SRT file."""
    # Prepend the 'library' directory to the file path for both the SRT and VTT files
    srt_file_path = srt_file_path.replace("\\", "/")
    vtt_file_path = vtt_file_path.replace("\\", "/")

    with open(srt_file_path, 'r', encoding='utf-8') as srt:
        lines = srt.readlines()

    with open(vtt_file_path, 'w', encoding='utf-8') as vtt:
        vtt.write("WEBVTT\n\n")
        for line in lines:
            # Convert timestamps (SRT format: 00:00:00,000 --> 00:00:01,000 to VTT format: 00:00:00.000 --> 00:00:01.000)
            line = line.replace(',', '.')
            vtt.write(line)

    # Delete the original SRT file after conversion
    if os.path.exists(srt_file_path):
        os.remove(srt_file_path)


def process_subtitle_file(file, root, extension):
    """Handles processing of SRT or VTT subtitles based on file type."""
    media_file_root_path = os.path.join(root, file).replace("\\", "/")
    

    if extension == ".srt":
        vtt_file_path = media_file_root_path.replace(".srt", ".vtt")
        convert_srt_to_vtt(media_file_root_path, vtt_file_path)
        subtitles = vtt_file_path
    elif extension == ".vtt":
        subtitles = media_file_root_path


    return subtitles


def extract_subtitles(file, root):
    # Create an output directory based on the video file name
    ffprobe_path = os.path.join(os.getcwd(), 'ffprobe.exe')
    ffmpeg_path = os.path.join(os.getcwd(), 'ffmpeg.exe')
    video_file = os.path.join(root, file).replace("\\", "/")

    if not os.path.exists(ffprobe_path):
        raise FileNotFoundError("ffprobe binary not found. Please ensure ffprobe is bundled with the application.")

    if not os.path.exists(ffmpeg_path):
        raise FileNotFoundError("ffmpeg binary not found. Please ensure ffmpeg is bundled with the application.")
    
    start_time = time.time()
    
    # Get subtitle streams info using ffprobe
    probe_cmd = [
        ffprobe_path,
        '-v', 'error',
        '-select_streams', 's', 
        '-show_entries', 'stream=index:stream_tags=title,language', 
        '-of', 'json',
        video_file
    ]
    
    result = subprocess.run(
        probe_cmd, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, 
        encoding='utf-8', errors='replace')

    # Parse the ffprobe output and extract subtitle streams
    try:
        subtitles = json.loads(result.stdout).get("streams", [])
    except json.JSONDecodeError as e:
        print("[ warning ] Error parsing FFprobe output:", e)
        return []

    extracted_files = []
    



    desired_languages = ['en', 'eng']

    # the most retarded shit ever, have to subtract starting index number, 
    #if you get Json output: [{'index': 3, 'tags': {'language': 'jpn', 'title': 'Forced'}}, {'index': 4,  
    # YOU HAVE to start from 'index': 0 but different files might have different starting indexes, so to correctly match to your desired sub you need index_zero...
    if subtitles:
        index_zero = subtitles[0].get("index") 

    # Process each subtitle stream
    for sub in subtitles:
        index = sub["index"]
        language = sub.get("tags", {}).get("language", "")

        if language.lower() not in [lang.lower() for lang in desired_languages]:
            continue

        output_dir = f'{root}/subs_{os.path.splitext(os.path.basename(file))[0]}'
        os.makedirs(output_dir, exist_ok=True)  # Ensure output directory exists

        # Output file path based on title
        output_file = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(video_file))[0]}_{index}{language}.vtt")
        
        # Prepare the ffmpeg command to extract the subtitles
        extract_cmd = [
            ffmpeg_path,
            '-i', video_file,  # Input video file
            f'-map', f'0:s:{index-index_zero}',  # Map subtitle stream by index
            '-c:s', 'webvtt',         # Convert to VTT format
            '-y',                     # Overwrite output file if it already exists
            output_file
        ]
        
        result = subprocess.run(
            extract_cmd, 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding='utf-8', errors='replace'
        )

        end_time = time.time()
        duration = end_time - start_time

        # Check for errors in the extraction process
        if result.returncode != 0:
            print("[ warning ] FFmpeg error:", result.stderr)
        # else:
        #     print(f"lang: {language}, index: {index} -- Subtitles extracted successfully in {duration:.3f}s :", result.stdout)


        extracted_files.append(output_file)
    
    # if not extracted_files:
    #     print("No subtitles extracted.")
    return extracted_files


def look_for_subtitles(media_file, root):
    """Look for subtitles (both SRT and VTT) for movies or series."""
    subtitle_folder_path = f'{root}/subs_{os.path.splitext(os.path.basename(media_file))[0]}'
    subtitles = []
    if os.path.exists(subtitle_folder_path):
        for root, _, files in os.walk(subtitle_folder_path):
            for file in files:
                if not (file.endswith(".srt") or file.endswith(".vtt")):
                    return []
                # print(f'[ debug ] Subtitles found -- {file}')
                subtitles.append(process_subtitle_file(file, root, os.path.splitext(file)[1].lower()))

    else:
        for root, _, files in os.walk(root):
            for file in files:
                if file.endswith(".srt") or file.endswith(".vtt"):
                    if os.path.splitext(os.path.basename(media_file))[0] == os.path.splitext(os.path.basename(file))[0]: # in case file doesnt have it's dedicated subtitle folder look for srt / vtt that match media file name
                        # print(f'[ debug ] Subtitles found -- {file}')
                        subtitles.append(process_subtitle_file(file, root, os.path.splitext(file)[1].lower()))

    return subtitles

def get_all_subtitles(file, root):
    """Combines existing and extracted subtitles into one list."""
    
    # Look for existing subtitles (SRT/VTT)
    existing_subtitles = look_for_subtitles(file, root)

    # If existing subtitles are found, return them
    if existing_subtitles:  
        return existing_subtitles
    
    # Otherwise, extract subtitles from the video file
    extracted_subtitles = extract_subtitles(file, root)

    return extracted_subtitles  # This could still be an empty list if extraction fails















def convert_duration(duration):
    # Assuming duration is in seconds and converting it to HH:MM:SS format
    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def bitrate_to_kbps(bitrate):
    # Assuming bitrate is in bps (bits per second)
    try:
        bitrate = int(bitrate)
        return bitrate / 1000  # Convert to kbps
    except (ValueError, TypeError):
        return 0  # Return 0 if the bitrate is invalid



def frame_rate_to_float(frame_rate):
    # Assuming frame_rate is in the form of "num/den" like "25/1"
    try:
        numerator, denominator = map(int, frame_rate.split('/'))
        return numerator / denominator
    except ValueError:
        return float(frame_rate)  # Fallback if it's already a decimal value




def get_video_metadata(file, root):
    ffprobe_path = os.path.join(os.getcwd(), 'ffprobe.exe') 
    video_path = os.path.join(root, file).replace("\\", "/")


    # Check if ffprobe binary exists
    if not os.path.exists(ffprobe_path):
        raise FileNotFoundError("ffprobe binary not found. Please ensure ffprobe is bundled with the application.")
    


    cmd = [
        ffprobe_path,
        '-v', 'error', 
        '-show_entries', 'format=duration,bit_rate', 
        '-show_entries', 'stream=codec_name,width,height,avg_frame_rate,codec_type', 
        '-of', 'json', 
        video_path
    ]


    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    metadata = json.loads(result.stdout.decode('utf-8'))
    
    return metadata



def ffmpeg_video_metadata(metadata):
    # Extract general metadata
    duration = metadata.get('format', {}).get('duration', None)
    bitrate = metadata.get('format', {}).get('bit_rate', None)
    
    # Extract video stream metadata
    video_stream = next((stream for stream in metadata.get('streams', []) if stream['codec_type'] == 'video'), None)
    width = video_stream.get('width', None) if video_stream else None
    height = video_stream.get('height', None) if video_stream else None
    frame_rate = video_stream.get('avg_frame_rate', None) if video_stream else None
    codec_video = video_stream.get('codec_name', None) if video_stream else None
    
    # Extract audio stream metadata
    audio_stream = next((stream for stream in metadata.get('streams', []) if stream['codec_type'] == 'audio'), None)
    codec_audio = audio_stream.get('codec_name', None) if audio_stream else None
    
    # Calculate Aspect Ratio (Width / Height)
    aspect_ratio = None
    if width and height:
        aspect_ratio = round(width / height, 2)
    
    # If frame rate exists, convert it to float
    frame_rate_float = None
    if frame_rate:
        frame_rate_float = frame_rate_to_float(frame_rate)

    duration_ = None
    if duration:
        duration_ = convert_duration(float(duration))

    # Return the video metadata in the desired format
    return {
        'resolution': f"{width}x{height}",
        'duration': duration_,
        'audio_codec': codec_audio,
        'video_codec': codec_video,
        'bitrate': "{:.2f} kbps".format(bitrate_to_kbps(bitrate)),
        'frame_rate': "{:.3f}".format(frame_rate_float) if frame_rate_float else None,
        'width': width,
        'height': height,
        'aspect_ratio': aspect_ratio,
    }