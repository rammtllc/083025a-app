import json

def extract_assistant_text(jsonl_lines):
    """Extract all assistant content from a list of JSONL lines."""
    texts = []
    for line in jsonl_lines:
        try:
            obj = json.loads(line)
            for msg in obj.get("messages", []):
                if msg.get("role") == "assistant":
                    texts.append(msg.get("content", "").strip())
        except json.JSONDecodeError:
            continue
    return texts

def sliding_window_dynamic(sentences, max_samples=9999):
    """
    Generate samples with a sliding window that:
    - Starts with the first sentence
    - Each new sample removes the last sentence of the previous sample
      and adds the next sentence
    """
    samples = []
    n = len(sentences)

    if n == 0:
        return samples

    # Start with first sentence
    current_window = [sentences[0]]
    samples.append(" / ".join(current_window))

    i = 1
    while i < n and len(samples) < max_samples:
        # Remove last sentence from previous window
        if len(current_window) > 1:
            current_window.pop(-1)

        # Add next sentence
        current_window.append(sentences[i])

        # Add new sample
        samples.append(" / ".join(current_window))

        i += 1

    return samples[:max_samples]

if __name__ == "__main__":
    INPUT_FILE = "output.jsonl"   # Your JSONL file
    OUTPUT_FILE = "samples.jsonl"
    MAX_SAMPLES = 9999

    # Load all lines from input JSONL
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Extract assistant sentences
    assistant_texts = extract_assistant_text(lines)

    # Generate dynamic sliding window samples
    samples = sliding_window_dynamic(assistant_texts, MAX_SAMPLES)

    # Write new JSONL with sliding-windowed assistant content
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for s in samples:
            record = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a parody song and lyric maker for YouTube videos, creating funny and engaging content."
                    },
                    {
                        "role": "user",
                        "content": "Write a section of a parody song in this style."
                    },
                    {
                        "role": "assistant",
                        "content": s
                    }
                ]
            }
            f.write(json.dumps(record) + "\n")

    print(f"✅ Generated {len(samples)} samples in {OUTPUT_FILE}")
