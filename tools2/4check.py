# -----------------------------
# Configuration
# -----------------------------
import os
import json
import time
from openai import OpenAI

# -----------------------------
# Configuration
# -----------------------------
API_KEY = ""
INPUT_FILE = "combiined.txt"
OUTPUT_FILE = "output.jsonl"
HARD_DELAY_SECONDS = 2

# -----------------------------
# Set environment variable for OpenAI API
# -----------------------------
os.environ["OPENAI_API_KEY"] = API_KEY
# -----------------------------
# OpenAI Client
# -----------------------------
client = OpenAI()  # Now it will read the API key from the environment
client = OpenAI(api_key=API_KEY)

# -----------------------------
# Moderation check
# -----------------------------
def check_line(text):
    try:
        response = client.moderations.create(
            model="omni-moderation-latest",
            input=text
        )
        result = response.results[0]
        return not result.flagged
    except Exception as e:
        print(f"❌ Moderation error: {e}")
        return False

# -----------------------------
# Process file
# -----------------------------
def process_file(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"❌ Input file '{input_file}' not found.")
        return

    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "a", encoding="utf-8") as outfile:

        for line_number, line in enumerate(infile, 1):
            line = line.strip()
            if not line:
                continue

            print(f"[Line {line_number}] Checking moderation...")
            if check_line(line):
                record = {"text": line}
                outfile.write(json.dumps(record, ensure_ascii=False) + "\n")
                print(f"[Line {line_number}] ✅ Accepted and written")
            else:
                print(f"[Line {line_number}] ⚠️ Flagged / skipped")

            time.sleep(HARD_DELAY_SECONDS)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    process_file(INPUT_FILE, OUTPUT_FILE)
    print(f"✅ Processing complete! JSONL saved to '{OUTPUT_FILE}'")
