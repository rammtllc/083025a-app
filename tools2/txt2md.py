from mido import MidiFile, MidiTrack, Message
import csv

mid = MidiFile()
track = MidiTrack()
mid.tracks.append(track)

ticks_per_sec = 480  # adjust as needed
last_tick = 0
last_note = None

with open("clean.txt") as f:
    reader = csv.DictReader(f)
    for row in reader:
        tick = int(float(row["time_seconds"]) * ticks_per_sec)
        note = int(row["note_midi"])
        if last_note is not None:
            track.append(Message('note_off', note=last_note, velocity=64, time=tick - last_tick))
        track.append(Message('note_on', note=note, velocity=64, time=0))
        last_tick = tick
        last_note = note

if last_note is not None:
    track.append(Message('note_off', note=last_note, velocity=64, time=last_tick))

mid.save("converted.mid")
