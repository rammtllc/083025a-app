# audio_to_midi.py
import librosa
import pretty_midi
import sys

def audio_to_midi(input_file, output_file="output.mid"):
    # Load audio
    y, sr = librosa.load(input_file)
    
    # Extract pitches and magnitudes
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    
    midi = pretty_midi.PrettyMIDI()
    piano = pretty_midi.Instrument(program=0)  # Acoustic Grand Piano
    
    # Iterate over frames
    for t in range(pitches.shape[1]):
        index = magnitudes[:, t].argmax()
        pitch = pitches[index, t]
        if pitch > 0:
            note_number = int(librosa.hz_to_midi(pitch))
            note = pretty_midi.Note(
                velocity=100, 
                pitch=note_number, 
                start=t/100, 
                end=(t+1)/100
            )
            piano.notes.append(note)
    
    midi.instruments.append(piano)
    midi.write(output_file)
    print(f"MIDI saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audio_to_midi.py <audio_file>")
    else:
        audio_to_midi(sys.argv[1])
