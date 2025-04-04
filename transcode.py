import time
from datetime import datetime
import subprocess
import os
import json


def remove_file_with_retry(file_path, retries=5, delay=1):
    """Attempt to remove a file with retries in case it's being used by another process."""
    for attempt in range(retries):
        try:
            os.remove(file_path)
            #print(f"[ info ] File removed successfully: {file_path}")
            return
        except PermissionError:
            if attempt < retries - 1:
                print(f"[ warning ] File is being used, retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"[ warning ] Failed to remove file after {retries} attempts: {file_path}")
                raise


def convert_to_mp4(file, root):
    if file.endswith(".mp4"):
        return False
    ffmpeg_path = os.path.join(os.getcwd(), 'ffmpeg.exe')
    start_time = time.time()
    file_path = os.path.join(root, file)
    output_file = os.path.splitext(file_path)[0] + ".mp4"

    # Ensure the output file doesn't already exist or is not locked
    if os.path.exists(output_file):
        # If the output file exists, add a unique timestamp to avoid overwriting
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = os.path.splitext(file_path)[0] + f"_{timestamp}.mp4"
        print(f'[ info ] Output file exists, using a unique filename: {output_file}')

    # Command for FFmpeg to convert the video, audio, and subtitle streams
    command = [
        ffmpeg_path,
        '-i', file_path,      # Input file
        '-codec', 'copy',      # Copy the video, audio, and subtitle streams (no re-encoding)
        '-f', 'mp4',           # Output format (MP4)
        output_file            # Output file (MP4)
    ]

    # FFmpeg with progress reporting
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


    # Attempt to remove the original file with retries
    remove_file_with_retry(file_path)



    end_time = time.time()
    duration = end_time - start_time
    print(f'[ debug ] {file} -- Converted to .mp4 in {duration:.3f}s')
    return os.path.basename(output_file)



def transcode_to_mp4_264_aac(file, root):
    time.sleep(1) # wait for watchdog
    print(f'\n[ debug ] {file} -- Transcoding to .mp4 x264 aac')
    start_time = time.time()

    ffmpeg_path = os.path.join(os.getcwd(), 'ffmpeg.exe')

    file_path = os.path.join(root, file)
    output_file = os.path.splitext(file_path)[0] + ".mp4"

    # Ensure the output file doesn't already exist or is not locked
    if os.path.exists(output_file):
        # If the output file exists, add a unique timestamp to avoid overwriting
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = os.path.splitext(file_path)[0] + f"_{timestamp}.mp4"
        print(f'[ debug ] Output file exists, using a unique filename: {output_file}')

    with open('watchdog_temp.txt', 'w') as f:       # Watchdog wont activcate for those files
        f.writelines([output_file + '\n', file_path + '\n'])

    
    # Command for FFmpeg to convert the video, audio, and subtitle streams
    # Using NVENC (NVIDIA GPU acceleration) for video and AAC for audio encoding
    command = [
        ffmpeg_path,
        '-i', file_path,
        '-c:v', 'h264_nvenc',       # Video codec using NVENC (GPU acceleration for NVIDIA)
        '-preset', 'fast',          # Encoding speed preset
        '-cq:v', '19',              # Set quality level (lower is better quality)
        '-pix_fmt', 'yuv420p',           # Force 8-bit color (no 10-bit support)
        '-c:a', 'aac',              # Audio codec (AAC)
        '-ac', '2',                 # Number of audio channels (stereo)
        '-f', 'mp4',                # Output format (MP4)
        output_file                 # Output file (MP4)
    ]

    try:
        # Using subprocess.Popen to get real-time progress updates from stderr
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')

        # Read stderr for progress info
        while True:
            stderr_line = process.stderr.readline()
            if stderr_line == '' and process.poll() is not None:
                break  

            if stderr_line:
                # Check for FFmpeg progress lines containing frame, time, fps, bitrate, etc.
                if 'frame=' in stderr_line:
                    try:
                        # Extract frame, fps, time, and bitrate info
                        frame_info = stderr_line.split('frame=')[-1].split(' ')[0]  # frame count
                        time_info = stderr_line.split('time=')[-1].split(' ')[0]   # time information
                        fps_info = stderr_line.split('fps=')[-1].split(' ')[0]     # fps value
                        bitrate_info = stderr_line.split('bitrate=')[-1].split(' ')[0]  # bitrate info
                        
                        # Format the output to match your desired format
                        print(f'frame={frame_info} fps={fps_info} time={time_info} bitrate={bitrate_info} speed={stderr_line.split("speed=")[-1].split("x")[0]}x -- {file}')

                    except Exception as e:
                        # Handle any parsing errors
                        print(f"[ warning ] Could not parse line: {stderr_line}. Error: {e}")

    except Exception as e:
        print(f"[ error ] An error occurred: {e}")

    remove_file_with_retry(file_path)

    end_time = time.time()
    duration = end_time - start_time
    print(f'[ debug ] {file} -- Transcoded to .mp4 x264 aac in {duration:.3f}s')

    return os.path.basename(output_file)
