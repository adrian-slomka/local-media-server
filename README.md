# Nvidia-Powered Media Server

A Python-based web application powered by Flask that serves as a media server similar to Plex or Jellyfin. This application is best used with machines with NVIDIA GPUs and requires the latest NVIDIA drivers for proper functionality. It automatically re-encodes media files to the widely-supported **x264 video codec** with **AAC audio** if they aren't already in this format. Please note that this app is intended for high-performance systems, and re-encoding can be resource-heavy.

## Web App Preview

![App Screenshot](https://raw.githubusercontent.com/adrian-slomka/local-media-server/main/app_preview/desktop_index_screenshot_preview.png)

![App Screenshot](https://raw.githubusercontent.com/adrian-slomka/local-media-server/main/app_preview/desktop_page_screenshot_preview.png)

![App Screenshot](https://raw.githubusercontent.com/adrian-slomka/local-media-server/main/app_preview/desktop_page_ep_screenshot_preview.png)

## Features

- **Web UI**: Decent looking and responsive web application with a dynamic search and watchlist feature.
- **database**: Movies and series are saved into light-weight sqlite3 database for simplicity and easy access.
- **tmdb api**: Integrated tmdb api requests that will provide user with some basic info and neat movie / series posters and their backdrops.
- **No tracking**: Unlike Plex, the app doesn't save device's physical address, nor it's name and does not have any kind of cookies or ads.

## Requirements

- **NVIDIA GPU**: This application is designed to run **exclusively on NVIDIA-powered machines for the NVENC encoding.
- **NVIDIA Drivers**: The most recent NVIDIA drivers are required to ensure compatibility with the re-encoding and media processing functions.
- **Python 3.8+**: Make sure Python is installed on your system. If not, you can download it from [python.org](https://www.python.org/downloads/).
- **FFmpeg**: A multimedia framework that handles video and audio conversions. This app relies on FFmpeg for re-encoding media files.

**with minor changes to the code it will run on any gpu.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/local-media-server.git
    ```

2. Create a [virtual environment](https://docs.python.org/3/library/venv.html) (optional but recommended):

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Make sure you have the latest **NVIDIA drivers** installed.

5. *Download **FFmpeg**: From [FFmpeg's official website](https://ffmpeg.org/download.html) download FFprobe.exe and FFmpeg.exe and drop them inside the app's main folder dir.

6. Acquire TMDB API KEY from [TMDB](https://developer.themoviedb.org/docs/getting-started). Next, create .env in main app folder and paste the API KEY there like so: API_KEY=YourKey

7. (optional) Create .bat for start up convinience:

    ```bash
    @echo off
    :: Activate the virtual environment
    call "%~dp0YourEnvName\Scripts\activate.bat"

    :: Run the app.py using the Python
    python "%~dp0app.py"

    pause
    ```

## Usage

1. Start the server:

    ```bash
    python app.py
    ```

    or via .bat file

2. The web application will be accessible on [http://localhost:8000](http://localhost:8000). Open this URL in your web browser. 
Additioanly, the app can be accessed on mobile devices when connected to the same wi-fi network:
- Get your hosting PC's local ip4 adress (open cmd and type: ipcofing and look for ipv4). 
- Next, on your mobile device connected to the same Wi-Fi network type that ip adress followed by :8000, example: 192.168.0.100:8000

3. To add your media files first create folder where you will store your movies or series. 
        
4. In the main app's folder, open settings.json and paste your path/s like so: "series": ["D:/Lib/series","D/lib/series_folder2"], (don't forget comma)

5. The app will scan new files on launch or dynamically and if needed will re-encoded incompatible files for html playback.

## Known Limitations

- **Re-encoding performance**: Since the app uses GPU acceleration, re-encoding large files or a large number of files can put a significant load on your system. Please ensure your machine has adequate resources (RAM, GPU power) for this task.
- **Subtitle extraction**: The app supports subtitle extraction for embedded subtitles in video files, but the extraction process is limited. Only **English subtitles** are extracted and supported at the moment. Additionally, some subtitle formats in containers like `.mp4` may not be handled perfectly.
- **File types**: While the app supports common video formats, it may have limited support for niche or less common file types. We recommend using **MP4** files for the best compatibility with the subtitle extraction and re-encoding features.
- **library path selection**: At the moment, path to your library folders cannot be added via mobile devices.
- **Bugs**: This is a very early version of this app.

## FAQ

### Does the app support other video formats besides MP4?
Yes, but **MP4** x264, aac is the most reliable format for compatibility with subtitle extraction and re-encoding. Other formats may work but will require re-encoding and may have issues with subtitle extraction.

### Can I run this app on a non-NVIDIA machine?
Yes. However it requries a small code change. Head to transcode.py and on the line 90 change "h264_nvenc" to "libx264" (libx264 is a CPU-based software encoder, it's way slower on large files compared to h264_nvenc.)

### What do I do if subtitles aren't being extracted properly?
If subtitles aren't extracted correctly from the embedded container (.mp4, .mkv etc): 
1) If the app is running: temporarily move that video file.mp4 outside of the library. If the app is not running: move that video file and start the app.
2) Download subtitles from openSubtitles or similar site and rename subtitle file so that it has the same name as video file. Example: video file -> "My_video.mp4", subtitle file -> "My_video.srt" or "My_video.vtt"
3) First, place the subtitle file in the same folder where you temporarily moved file.mp4
4) Move back file.mp4 and wait for the app to re-scan



**Note:** This is a high-performance, GPU-intensive application. Use it on a machine with adequate resources for the best experience.
**Note2:** I'm a college student and this is strictly a learning project. 
