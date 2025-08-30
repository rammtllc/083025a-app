# transcript_utils.py

import re
import statistics

def parse_transcript1(input_file, output_file, default_gap=1.0, max_sentence_duration=15.0):
    """
    Parse a word-level transcript into sentences using punctuation, pauses, and capital letters.

    Args:
        input_file (str): Path to the transcript file with timestamps.
        output_file (str): Path to save the parsed sentences.
        default_gap (float): Minimum pause (seconds) to consider a sentence break.
        max_sentence_duration (float): Maximum duration (seconds) for a sentence.
    """
    words = []
    timestamps = []

    # Read transcript
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"(\d+\.\d+)\s+(.*)", line.strip())
            if not match:
                continue
            ts, word = match.groups()
            timestamps.append(float(ts))
            words.append(word)

    # Calculate median gap for adaptive threshold
    gaps = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
    median_gap = statistics.median(gaps) if gaps else default_gap
    threshold = max(default_gap, median_gap * 2)

    sentences = []
    current_sentence = []
    sentence_start_time = None

    for i, word in enumerate(words):
        ts = timestamps[i]

        if not current_sentence:
            sentence_start_time = ts

        # Start new sentence if capital letter (not first word)
        if current_sentence and re.match(r"^[A-Z]", word):
            sentences.append(f"{sentence_start_time:.2f}  {' '.join(current_sentence)}")
            current_sentence = []
            sentence_start_time = ts

        current_sentence.append(word)

        # Determine next gap
        next_gap = (timestamps[i + 1] - ts) if i + 1 < len(timestamps) else 0
        sentence_duration = ts - sentence_start_time

        # Sentence boundary conditions
        if re.search(r"[.?!]$", word) or next_gap >= threshold or sentence_duration >= max_sentence_duration:
            sentences.append(f"{sentence_start_time:.2f}  {' '.join(current_sentence)}")
            current_sentence = []
            sentence_start_time = None

    # Catch leftover words
    if current_sentence:
        sentences.append(f"{sentence_start_time:.2f}  {' '.join(current_sentence)}")

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        for s in sentences:
            f.write(s + "\n")


# Optional CLI interface for standalone usage
if __name__ == "__main__":
    import sys
    import os

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

    base_name = input_file[:-9] if input_file.endswith("-word.txt") else input_file
    output_file = f"{base_name}-capitals.txt"

    parse_transcript(input_file, output_file)
    print(f"✅ Finished! Check '{output_file}'")
