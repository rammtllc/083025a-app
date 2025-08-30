import json
import re
import random
import numpy as np

def extract_sentences_from_assistant(jsonl_lines):
    """Extract all sentences from assistant content."""
    sentences = []
    for line in jsonl_lines:
        try:
            obj = json.loads(line)
            for msg in obj.get("messages", []):
                if msg.get("role") == "assistant":
                    text = msg.get("content", "").strip()
                    splits = re.split(r'(?<=[.!?])\s+', text)
                    sentences.extend([s.strip() for s in splits if s.strip()])
        except json.JSONDecodeError:
            continue
    return sentences

def weighted_indices(n):
    """Generate weight array biased toward start and end."""
    if n == 0:
        return []
    weights = np.array([min(i+1, n-i) for i in range(n)], dtype=float)
    weights /= weights.sum()
    return weights

def sliding_window_biased_with_removal(sentences, min_window=2, max_window=5, max_samples=9999):
    """
    Generate multi-sentence samples:
    - Sliding window with removal from previous window
    - Wrap-around weighted mixing
    """
    samples = []
    n = len(sentences)
    if n == 0:
        return samples

    weights = weighted_indices(n)

    # Start with first window
    window_size = random.randint(min_window, max_window)
    current_window = sentences[:window_size]
    samples.append(" / ".join(current_window))

    while len(samples) < max_samples:
        # Remove first sentence if window is longer than 1
        if len(current_window) > 1:
            current_window.pop(0)

        # Pick a new sentence biased toward start and end
        idx = np.random.choice(n, p=weights)
        current_window.append(sentences[idx])

        samples.append(" / ".join(current_window))

    return samples[:max_samples]

if __name__ == "__main__":
    INPUT_FILE = "output.jsonl"
    OUTPUT_FILE = "samples_9999.jsonl"
    MAX_SAMPLES = 9999

    # Load JSONL
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Extract assistant sentences
    sentences = extract_sentences_from_assistant(lines)
    print(f"🔹 Extracted {len(sentences)} sentences.")

    # Generate biased sliding window with removal samples
    samples = sliding_window_biased_with_removal(
        sentences, min_window=2, max_window=5, max_samples=MAX_SAMPLES
    )
    print(f"🔹 Generated {len(samples)} samples.")

    # Save to JSONL
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
