#!/usr/bin/env python3
"""
remove_vocals.py
----------------
Remove vocals from an MP3 file using Spleeter (2 stems: vocals + instrumental).
Outputs the instrumental as a WAV file.
"""

import os
import sys
from spleeter.separator import Separator
from spleeter.audio.adapter import AudioAdapter

def remove_vocals(input_file: str, output_dir: str = "output"):
    """
    Remove vocals from an MP3 file and save instrumental to output_dir.

    :param input_file: Path to the input MP3 file
    :param output_dir: Directory to save the instrumental
    """
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' does not exist.")
        return

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Initialize Spleeter separator (2 stems: vocals + accompaniment)
    separator = Separator('spleeter:2stems')

    print(f"Processing '{input_file}'...")

    # Load audio
    audio_loader = AudioAdapter.default()
    waveform, sr = audio_loader.load(input_file, sample_rate=44100)

    # Perform separation
    prediction = separator.separate(waveform)

    # Save instrumental
    instrumental_path = os.path.join(output_dir, "instrumental.wav")
    audio_loader.save(instrumental_path, prediction['accompaniment'], sr)
    
    print(f"Instrumental saved to: {instrumental_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python remove_vocals.py <input_file.mp3> [output_dir]")
        sys.exit(1)

    input_mp3 = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 else "output"

    remove_vocals(input_mp3, output_directory)
