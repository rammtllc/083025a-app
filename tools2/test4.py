import json
import re
import random

def extract_sentences_from_assistant(jsonl_lines):
    """Extract all sentences from assistant content."""
    sentences = []
    for line in jsonl_lines:
        try:
            obj = json.loads(line)
            for msg in obj.get("messages", []):
                if msg.get("role") == "assistant":
                    text = msg.get("content", "").strip()
                    # Split into sentences using punctuation
                    splits = re.split(r'(?<=[.!?])\s+', text)
                    sentences.extend([s.strip() for s in splits if s.strip()])
        except json.JSONDecodeError:
            continue
    return sentences

def sliding_window_multi(sentences, min_window=2, max_window=5, max_samples=9999):
    """
    Generate overlapping multi-sentence samples.
    - Each sample length is random between min_window and max_window.
    - Slide forward: remove some from start, add next sentences.
    """
    samples = []
    n = len(sentences)
    if n == 0:
        return samples

    i = 0
    while len(samples) < max_samples and i < n:
        window_size = random.randint(min_window, max_window)
        # Make sure we don't go out of bounds
        window_sentences = sentences[i:i + window_size]
        if not window_sentences:
            break
        samples.append(" / ".join(window_sentences))
        # Move start forward by 1 sentence for next sliding window
        i += 1

    return samples[:max_samples]

if __name__ == "__main__":
    INPUT_FILE = "output.jsonl"
    OUTPUT_FILE = "samples.jsonl"
    MAX_SAMPLES = 9999

    # Load JSONL
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Extract all assistant sentences
    sentences = extract_sentences_from_assistant(lines)
    print(f"🔹 Extracted {len(sentences)} sentences.")

    # Generate multi-sentence sliding window samples
    samples = sliding_window_multi(sentences, min_window=2, max_window=5, max_samples=MAX_SAMPLES)
    print(f"🔹 Generated {len(samples)} sliding window samples.")

    # Write new JSONL
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for s in samples:
            record = {
                "messages": [
                    {"role": "system", "content": "You are a parody song and lyric maker for YouTube videos, creating funny and engaging content."},
                    {"role": "user", "content": "Write a section of a parody song in this style."},
                    {"role": "assistant", "content": s}
                ]
            }
            f.write(json.dumps(record) + "\n")

    print(f"✅ Saved {len(samples)} samples to {OUTPUT_FILE}")
