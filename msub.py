import subprocess
import re
import os

def mergeSub(type, inputvideo, sub, output="output.mp4", progress_callback=None):
    """
    Merge subtitles into a video with progress updates.

    Args:
        type (int): 
            1 = Mux (MKV), 
            2 = Mux (MP4 mov_text), 
            3 = Burn-in (CPU), 
            4 = Burn-in (GPU), 
            5 = Burn-in (Low CPU).
        inputvideo (str): Path to the input video file.
        sub (str): Path to the subtitle file (.srt or .ass).
        output (str, optional): Output file name. Defaults to "output.mp4".
        progress_callback (function, optional): Function to handle progress updates. Defaults to None.

    Returns:
        bool: True if successful, False if an error occurs.
    """
    if not os.path.exists(inputvideo):
        print(f"Error: Video file not found -> {inputvideo}")
        return False
    if not os.path.exists(sub):
        print(f"Error: Subtitle file not found -> {sub}")
        return False

    try:
        if type == 1:
            # Type 1: Soft Mux (Fastest, MKV recommended)
            output = output.replace(".mp4", ".mkv")
            command = [
                "ffmpeg", "-i", inputvideo, "-i", sub, 
                "-map", "0", "-map", "1", "-c", "copy", output
            ]
        
        elif type == 2:
            # Type 2: Soft Mux for MP4 (mov_text format)
            command = [
                "ffmpeg", "-i", inputvideo, "-i", sub,
                "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text", output
            ]

        elif type == 3:
            # Type 3: Hard Burn-in (Slow, CPU Only)
            command = [
                "ffmpeg", "-i", inputvideo, 
                "-vf", f"subtitles={sub}", 
                "-c:v", "libx264", "-preset", "ultrafast", 
                "-c:a", "copy", output
            ]

        elif type == 4:
            # Type 4: Hard Burn-in with GPU Acceleration (NVIDIA)
            command = [
                "ffmpeg", "-hwaccel", "cuda", "-i", inputvideo, 
                "-vf", f"subtitles={sub}", 
                "-c:v", "h264_nvenc", "-preset", "fast", "-b:v", "2M", 
                "-c:a", "copy", output
            ]

        elif type == 5:
            # Type 5: Burn-in with Reduced Resolution (For Low-End CPUs)
            command = [
                "ffmpeg", "-i", inputvideo, 
                "-vf", f"scale=1280:-2,subtitles={sub}", 
                "-c:v", "libx264", "-preset", "ultrafast", 
                "-c:a", "copy", output
            ]
        
        else:
            print("Invalid type. Use 1-5.")
            return False

        # Run FFmpeg and capture progress
        process = subprocess.Popen(
            command, stderr=subprocess.PIPE, universal_newlines=True
        )

        duration = None  # Total duration of the video
        for line in process.stderr:
            # Extract duration of the video
            if "Duration" in line and duration is None:
                match = re.search(r"Duration: (\d+):(\d+):(\d+.\d+)", line)
                if match:
                    hours, minutes, seconds = map(float, match.groups())
                    duration = hours * 3600 + minutes * 60 + seconds
            
            # Extract progress information
            if "time=" in line:
                match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
                if match and duration:
                    hours, minutes, seconds = map(float, match.groups())
                    elapsed = hours * 3600 + minutes * 60 + seconds
                    percentage = (elapsed / duration) * 100

                    # Extract speed and ETA
                    speed_match = re.search(r"speed=([\d.]+)x", line)
                    speed = float(speed_match.group(1)) if speed_match else 1.0
                    eta = (duration - elapsed) / speed if speed > 0 else 0

                    # Format ETA into minutes and seconds
                    eta_minutes = int(eta // 60)
                    eta_seconds = int(eta % 60)

                    # Call progress callback function
                    if progress_callback:
                        progress_callback(
                            percentage=round(percentage, 2),
                            speed=round(speed, 2),
                            eta=f"{eta_minutes}m {eta_seconds}s"
                        )

        process.wait()
        if process.returncode == 0:
            print(f"✅ Subtitle merged successfully! Output: {output}")
            return True
        else:
            print("❌ FFmpeg process failed.")
            return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


# Example usage
#if __name__ == "__main__":
    #def progress_update(percentage, speed, eta):
        #print(f"Progress: {percentage}% | Speed: {speed}x | ETA: {eta}")

    #mergeSub(
        #type=3,  # Change type to test different methods
        #inputvideo="video.mp4",
        #sub="subtitles.srt",
        #progress_callback=progress_update
  #)
