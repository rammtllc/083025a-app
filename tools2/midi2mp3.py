# wav_to_text.py
import sys
import numpy as np
from aubio import source, pitch

if len(sys.argv) < 3:
    print("Usage: python wav_to_text.py input.wav output.txt")
    sys.exit(1)

input_wav = sys.argv[1]
output_txt = sys.argv[2]

samplerate = 44100
win_s = 2048
hop_s = 512

s = source(input_wav, samplerate, hop_s)
pitch_o = pitch("yin", win_s, hop_s, samplerate)
pitch_o.set_unit("midi")
pitch_o.set_silence(-40)

with open(output_txt, "w") as f:
    f.write("time_seconds,note_midi,confidence\n")
    
    total_frames = 0
    while True:
        samples, read = s()
        if len(samples) < hop_s:
            samples = np.pad(samples, (0, hop_s - len(samples)), mode='constant')
        
        pitch_midi = pitch_o(samples)[0]
        confidence = pitch_o.get_confidence()
        time_sec = total_frames / samplerate
        
        # Only write confident pitches
        if confidence > 0.8 and pitch_midi > 0:
            f.write(f"{time_sec:.4f},{int(round(pitch_midi))},{confidence:.2f}\n")
        
        total_frames += read
        if read < hop_s:
            break

print(f"Pitch data saved to {output_txt}")
