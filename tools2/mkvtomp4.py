import subprocess
import sys
import os

def convert_mkv_to_mp4_and_mp3(input_file, output_mp4=None, output_mp3=None):
    if not os.path.isfile(input_file):
        print(f"File not found: {input_file}")
        return

    base_name = os.path.splitext(input_file)[0]

    if output_mp4 is None:
        output_mp4 = base_name + ".mp4"
    if output_mp3 is None:
        output_mp3 = base_name + ".mp3"

    # Convert MKV to MP4 (video + audio copy)
    command_mp4 = [
        "ffmpeg",
        "-i", input_file,
        "-c:v", "copy",
        "-c:a", "copy",
        output_mp4
    ]

    # Extract audio as MP3
    command_mp3 = [
        "ffmpeg",
        "-i", input_file,
        "-q:a", "0",  # best quality
        "-map", "a",
        output_mp3
    ]

    try:
        subprocess.run(command_mp4, check=True)
        print(f"MP4 conversion successful: {output_mp4}")

        subprocess.run(command_mp3, check=True)
        print(f"MP3 extraction successful: {output_mp3}")

    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert.py <input_file.mkv> [output_file.mp4] [output_file.mp3]")
    else:
        input_file = sys.argv[1]
        output_mp4 = sys.argv[2] if len(sys.argv) > 2 else None
        output_mp3 = sys.argv[3] if len(sys.argv) > 3 else None
        convert_mkv_to_mp4_and_mp3(input_file, output_mp4, output_mp3)
