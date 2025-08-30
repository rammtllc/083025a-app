# remix_midi.py
import pretty_midi
import sys
import random

# List of instruments for remixing (General MIDI program numbers)
REMIX_INSTRUMENTS = [0, 24, 40, 41, 42, 46, 56, 73]  # Piano, Guitar, Strings, Choir, Flute, etc.

def remix_midi(input_file, output_file="remix_output.mid", transpose_range=(-5, 5)):
    # Load original MIDI
    midi_data = pretty_midi.PrettyMIDI(input_file)
    
    remixed_midi = pretty_midi.PrettyMIDI()

    for i, instrument in enumerate(midi_data.instruments):
        # Pick a new instrument for the track
        new_program = REMIX_INSTRUMENTS[i % len(REMIX_INSTRUMENTS)]
        new_instrument = pretty_midi.Instrument(program=new_program, is_drum=instrument.is_drum)
        
        for note in instrument.notes:
            # Randomly transpose note within given range
            transpose = random.randint(transpose_range[0], transpose_range[1])
            new_pitch = max(0, min(127, note.pitch + transpose))
            
            # Randomize velocity slightly
            new_velocity = max(20, min(127, note.velocity + random.randint(-15, 15)))
            
            # Optionally randomize start time slightly
            new_start = note.start + random.uniform(-0.05, 0.05)
            new_end = max(new_start + 0.05, note.end + random.uniform(-0.05, 0.05))
            
            new_note = pretty_midi.Note(
                velocity=new_velocity,
                pitch=new_pitch,
                start=new_start,
                end=new_end
            )
            new_instrument.notes.append(new_note)
        
        remixed_midi.instruments.append(new_instrument)
    
    # Write remixed MIDI
    remixed_midi.write(output_file)
    print(f"Remixed MIDI saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python remix_midi.py <input_midi_file>")
    else:
        remix_midi(sys.argv[1])
