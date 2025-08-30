import sys
import aubio
import numpy as np
from mido import Message, MidiFile, MidiTrack

def wav_to_midi(wav_file, midi_file, hop_size=512, samplerate=44100):
    # Initialize aubio pitch detection
    pitch_o = aubio.pitch("yin", 2048, hop_size, samplerate)
    pitch_o.set_unit("midi")
    pitch_o.set_silence(-40)

    # Open the WAV file
    s = aubio.source(wav_file, samplerate, hop_size)
    samplerate = s.samplerate

    pitches = []
    confidences = []

    while True:
        samples, read = s()
        pitch = pitch_o(samples)[0]
        confidence = pitch_o.get_confidence()
        pitches.append(pitch)
        confidences.append(confidence)
        if read < hop_size:
            break

    # Convert to MIDI messages
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    prev_pitch = None
    time_per_hop = hop_size / samplerate
    ticks_per_beat = mid.ticks_per_beat
    velocity = 100

    for i, pitch in enumerate(pitches):
        if confidences[i] < 0.8:
            pitch = 0  # Treat low-confidence as rest
        if pitch != prev_pitch and prev_pitch is not None:
            # Note off for previous note
            if prev_pitch != 0:
                track.append(Message('note_off', note=int(prev_pitch), velocity=0, time=int(ticks_per_beat * time_per_hop)))
        if pitch != prev_pitch and pitch != 0:
            # Note on for new note
            track.append(Message('note_on', note=int(pitch), velocity=velocity, time=0))
        prev_pitch = pitch

    mid.save(midi_file)
    print(f"Converted {wav_file} → {midi_file} successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python wav_to_midi.py input.wav output.mid")
        sys.exit(1)
    wav_file = sys.argv[1]
    midi_file = sys.argv[2]
    wav_to_midi(wav_file, midi_file)
