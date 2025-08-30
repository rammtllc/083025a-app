import json

# Input and output JSON files
input_file = "input.jsonl"   # your JSON file with {"text": "..."} per line
output_file = "output.jsonl"  # .jsonl is the preferred format for fine-tuning

# Open the output file for writing in JSONL format
with open(output_file, "w") as out_f:
    with open(input_file, "r") as in_f:
        for line in in_f:
            try:
                data = json.loads(line.strip())
                text = data.get("text", "")
                # Remove the timestamp (everything before the first space)
                _, content = text.split(maxsplit=1)

                # Create a fine-tuning JSON object
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
                            "content": content
                        }
                    ]
                }

                # Write the JSON object as a single line
                out_f.write(json.dumps(record) + "\n")

            except Exception as e:
                print(f"Skipping line due to error: {line.strip()} ({e})")

print(f"JSONL file saved as {output_file}")
