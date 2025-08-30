import pygame
import os
import subprocess
import sys

# -----------------------------
# Media Conversion Utilities
# -----------------------------

def convert_mkv_to_mp4_and_mp3(input_file, output_mp4=None, output_mp3=None):
    """Convert MKV file to MP4 and extract MP3 audio using ffmpeg."""
    if not os.path.isfile(input_file):
        print(f"File not found: {input_file}")
        return

    base_name = os.path.splitext(input_file)[0]

    if output_mp4 is None:
        output_mp4 = base_name + ".mp4"
    if output_mp3 is None:
        output_mp3 = base_name + ".mp3"

    command_mp4 = [
        "ffmpeg",
        "-i", input_file,
        "-c:v", "copy",
        "-c:a", "copy",
        output_mp4
    ]

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


# -----------------------------
# Pygame Asset Utilities
# -----------------------------

def load_image(path, scale=None):
    """
    Load an image with optional scaling.
    Returns a Pygame Surface.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Image file not found: {path}")

    image = pygame.image.load(path).convert_alpha()

    if scale is not None:
        image = pygame.transform.smoothscale(image, scale)

    return image


def load_large_gear():
    """Load a large gear image."""
    return load_image("media/large_gear.png", scale=(200, 200))


def load_small_gear():
    """Load a small gear image."""
    return load_image("media/small_gear.png", scale=(80, 80))
