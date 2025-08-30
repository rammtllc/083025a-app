# Install dependencies first:
# pip install pyFluidSynth pydub

import subprocess
from pydub import AudioSegment
import fluidsynth

# Paths
midi_file = "vocals.mid"
soundfont = "FluidR3_GM.sf2"  # Download a .sf2 soundfont
wav_file = "vocalsoutput.wav"
mp3_file = "vocalsoutput.mp3"

# Step 1: Convert MIDI -> WAV using FluidSynth CLI
subprocess.run([
    "fluidsynth",
    "-ni",            # non-interactive
    soundfont,
    midi_file,
    "-F", wav_file    # output file
], check=True)

# Step 2: Convert WAV -> MP3 using pydub
sound = AudioSegment.from_wav(wav_file)
sound.export(mp3_file, format="mp3")

print("Conversion complete:", mp3_file)
