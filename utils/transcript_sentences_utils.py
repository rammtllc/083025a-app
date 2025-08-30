# transcript_utils.py

import re
import os
import sys

def parse_transcript2(input_file, output_file):
    """
    Parse a word-level transcript into sentences using punctuation as sentence boundaries.

    Args:
        input_file (str): Path to the transcript file with timestamps.
        output_file (str): Path to save the parsed sentences.
    """
    sentences = []
    current_sentence = []
    current_time = None

    # Read the file
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"(\d+\.\d+)\s+(.*)", line.strip())
            if not match:
                continue

            timestamp, word = match.groups()

            # If this is the first word of a sentence, store its timestamp
            if not current_sentence:
                current_time = timestamp

            current_sentence.append(word)

            # Check if the word ends a sentence
            if re.search(r"[.?!]$", word):
                full_sentence = " ".join(current_sentence)
                sentences.append(f"{current_time}  {full_sentence}")
                current_sentence = []
                current_time = None

    # If any leftover words without punctuation, output them as well
    if current_sentence:
        full_sentence = " ".join(current_sentence)
        sentences.append(f"{current_time}  {full_sentence}")

    # Save output
    with open(output_file, "w", encoding="utf-8") as f:
        for s in sentences:
            f.write(s + "\n")


# Optional CLI interface for standalone usage
if __name__ == "__main__":
    # Get input file from command line or prompt
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    else:
        input_file = input("Enter the input transcript file path (with -word.txt): ").strip()
        if not input_file:
            print("❌ Input file path is required.")
            sys.exit(1)

    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        sys.exit(1)

    # Automatically generate output file name with -sentence.txt
    base_name = input_file
    if input_file.endswith("-word.txt"):
        base_name = input_file[:-9]  # remove "-word.txt"
    output_file = f"{base_name}-sentence.txt"

    parse_transcript(input_file, output_file)
    print(f"✅ Finished! Check '{output_file}'")
