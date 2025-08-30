# enhance_midi.py
import pretty_midi
import sys

# Map original instruments to “better” ones
# You can change the MIDI program numbers for different sounds
# Example: 0 = Acoustic Grand Piano, 24 = Nylon Guitar, 40 = Violin
ENHANCED_INSTRUMENTS = [0, 24, 40, 41, 42, 46]  # Piano, Guitar, Strings, etc.

def enhance_midi(input_file, output_file="enhanced_output.mid"):
    # Load original MIDI
    midi_data = pretty_midi.PrettyMIDI(input_file)
    
    enhanced_midi = pretty_midi.PrettyMIDI()

    # Iterate through original instruments
    for i, instrument in enumerate(midi_data.instruments):
        # Pick a new instrument program (rotate if more instruments than available)
        new_program = ENHANCED_INSTRUMENTS[i % len(ENHANCED_INSTRUMENTS)]
        new_instrument = pretty_midi.Instrument(program=new_program, is_drum=instrument.is_drum)
        
        # Copy notes
        for note in instrument.notes:
            new_note = pretty_midi.Note(
                velocity=note.velocity,
                pitch=note.pitch,
                start=note.start,
                end=note.end
            )
            new_instrument.notes.append(new_note)
        
        enhanced_midi.instruments.append(new_instrument)
    
    # Write new MIDI file
    enhanced_midi.write(output_file)
    print(f"Enhanced MIDI saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python enhance_midi.py <input_midi_file>")
    else:
        enhance_midi(sys.argv[1])
