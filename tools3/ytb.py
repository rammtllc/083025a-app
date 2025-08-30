import yt_dlp
import sys
import os

def download_mp3(url, output_filename):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_filename,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == '__main__':
    # Get URL from command line or prompt
    if len(sys.argv) >= 2:
        url = sys.argv[1]
    else:
        url = input("Enter the YouTube URL: ").strip()
        if not url:
            print("❌ URL is required.")
            sys.exit(1)

    # Extract video ID from URL
    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    else:
        # fallback if URL format is youtu.be/ID
        video_id = url.split("/")[-1].split("?")[0]

    output_file = f"{video_id}.mp3"

    download_mp3(url, output_file)
    print(f"✅ MP3 saved as: {output_file}")
