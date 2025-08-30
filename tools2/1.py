import csv
from mido import Message, MidiFile, MidiTrack, MetaMessage

# CSV file containing your data
csv_file = 'clean.txt'
# Output MIDI file
midi_file = 'cleeanoutput.mid'

# Create a new MIDI file and a track
mid = MidiFile()
track = MidiTrack()
mid.tracks.append(track)

# Set tempo (optional, 500000 microseconds per beat = 120 BPM)
track.append(MetaMessage('set_tempo', tempo=500000))

# Read the CSV data
with open(csv_file, 'r') as f:
    reader = csv.DictReader(f)
    previous_time = 0
    for row in reader:
        time_seconds = float(row['time_seconds'])
        note = int(row['note_midi'])
        # Convert time from seconds to ticks (assuming 480 ticks per beat)
        # ticks = seconds * (ticks_per_beat / seconds_per_beat)
        # seconds_per_beat = 0.5 for 120 BPM (1 beat = 0.5s)
        ticks = int((time_seconds - previous_time) * 960)  # 960 ticks per second as approximation
        previous_time = time_seconds
        velocity = int(float(row['confidence']) * 127)  # scale confidence to 0-127

        # Add note on and off (short note duration here, e.g., 100 ticks)
        track.append(Message('note_on', note=note, velocity=velocity, time=ticks))
        track.append(Message('note_off', note=note, velocity=0, time=100))

# Save MIDI file
mid.save(midi_file)
print(f"MIDI file saved as {midi_file}")
