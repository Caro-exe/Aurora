from pathlib import Path # FOR THE STUPID PATHS
import subprocess # DLP extension stuff
import cv2 # FOR VIDEO RESIZING
import numpy as np # LETS CALCULATE THE BRIGHTNESS STUFFS
from yt_dlp import YoutubeDL #The one and only yt-dlp library



def download_video(video_url):
    output_folder = Path("videos")
    output_folder.mkdir(exist_ok=True)

    ydl_opts = {
        # Get the video without the sound
        "format": "bestvideo[height<=360]/bestvideo",

        # Name the video after its youtube ID
        "outtmpl": str(output_folder / "%(id)s.%(ext)s"),

        "noplaylist": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)

        # Get the actual file yt-dlp downloaded
        downloaded_file = Path(ydl.prepare_filename(info))

    print("Downloaded:", downloaded_file)

    return downloaded_file


def resize_video(input_file):
    output_folder = Path("videos")

    resized_file = output_folder / f"{input_file.stem}_small.mp4"

    command = [
        "ffmpeg",

        # Input file
        "-i", str(input_file),

        # Resize width to 300px, preserve aspect ratio
        "-vf", "scale=300:-2",

        # Remove audio
        "-an",

        # Encode as H.264 MP4
        "-c:v", "libx264",

        # Overwrite output if it already exists
        "-y",

        str(resized_file),
    ]

    subprocess.run(command, check=True)

    print("Resized:", resized_file)

    return resized_file


def prepare_video(video_url):
    original = download_video(video_url)
    resized = resize_video(original)

    return resized

def read_video(video_path):
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        print("Upps sorreh video not opening :<")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print("FPS:", fps)
    print("Frame Count:", frame_count)

    frames_read = 0

    # The chicken cannot be laid before its egg 
    prev_lum = None
    flashes = []

    while True:

        success, frame = cap.read()

        if not success:
            break

        # Get digital luminance-ish value of every pixel
        digi_lum = frame.mean(axis=2)

        # Convert to estimated luminance in cd/m²
        lum = 413.435 * (
            0.002745 * digi_lum + 0.0189623
        ) ** 2.2

        # We can only calculate a difference
        # if a previous frame exists
        if prev_lum is not None:

            # Difference between current and previous frame
            batman = lum - prev_lum

            brightening_pixels = np.sum(batman >= 20)
            darkening_pixels = np.sum(batman <= -20)
            total_pixels = batman.size
            brightening_fraction = brightening_pixels / total_pixels
            darkening_fraction = darkening_pixels / total_pixels
            timestamp = frames_read / fps

            upsidedown = 0.25

            bflash = brightening_fraction >= upsidedown
            dflash = darkening_fraction >= upsidedown

            if bflash:
                flashes.append({
                    "time": timestamp,
                    "frames": frames_read,
                    "type": "+",
                    "area": brightening_fraction  })

            if dflash:
                flashes.append({
                    "time": timestamp,
                    "frames": frames_read,
                    "type": "-",
                    "area": darkening_fraction
                })


        

        
            

            

        

        # Current frame becomes previous frame
        # for the NEXT loop
        prev_lum = lum

        frames_read += 1

    cap.release()
    zigzags = []

    for i in range(1, len(flashes)):
        prev = flashes[i - 1]
        curr = flashes[i]

        if prev["type"] != curr["type"]:
            timegap  = (curr["time"] - prev["time"])
        zigzags.append({
            "start": prev["time"],
            "s-type": prev["type"],
            "end": curr["time"],
            "e-type": curr["type"],
            "duration": timegap,

        })



    print ("Important light changes:")
    for event in flashes[:20]:
        print(
            round(event["time"], 3),
            "seconds",
            event["type"],
            round(event["area"] * 100, 2),
            "%"
        )

    print ("zigzags:")
    
    for event in zigzags:
        print(
            round(event["start"], 3),
            "to",
            round(event["end"], 3),
            "seconds",
            event["s-type"],
            "to",
            event["e-type"]
        )

    print("Frames the book worm has swallowed:", frames_read)



if __name__ == "__main__":
    url = input("Enter YouTube URL: ").strip()

    final_video = prepare_video(url)

    print("video squashed:")
    print(final_video)
    read_video(final_video)

    