import json
import openai
import time
import os
import glob
import sys

# Set your OpenAI API key
openai.api_key = "YOUR_API_KEY"

def suggest_question_for_text(text):
    prompt = (
        "Given the following text, generate a single, concise question about it. "
        "Respond with only the question, no explanations or extra text.\n\n"
        f"Text: \"{text}\""
    )
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=50,
        )
        question = response.choices[0].message.content.strip()
        if not question.endswith('?'):
            question += '?'
        return question
    except Exception as e:
        print(f"API error: {e}")
        return None

def generate_fine_tune_jsonl(
    input_txt_path,
    output_jsonl_path,
    rolling_lines=3,
    rolling_chars=None,
    sliding_window=False
):
    previous_lines = []

    with open(input_txt_path, 'r', encoding='utf-8') as infile, \
         open(output_jsonl_path, 'a', encoding='utf-8') as outfile:

        for line in infile:
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                continue
            timestamp, text = parts[0], parts[1]

            # Remove duplicates from rolling context
            unique_previous = [l for l in previous_lines[-rolling_lines:] if l != text]

            if sliding_window:
                combined_context = " ".join(unique_previous)
                if rolling_chars:
                    combined_context = combined_context[-rolling_chars:]
                combined_text = (combined_context + " " + text).strip()
            else:
                combined_text = " ".join(unique_previous + [text]).strip()
                if rolling_chars and len(combined_text) > rolling_chars:
                    combined_text = combined_text[-rolling_chars:]

            # Standard system + user messages
            record = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a YouTube scriptwriter who tells engaging personal stories in a casual and motivational style."
                    },
                    {
                        "role": "user",
                        "content": "Write a section of a YouTube video script in this style."
                    },
                    {
                        "role": "assistant",
                        "content": combined_text
                    }
                ]
            }

            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")
            previous_lines.append(text)
            time.sleep(1)

if __name__ == "__main__":
    # Determine prefix from command line or console input
    if len(sys.argv) > 1:
        prefix = sys.argv[1]
    else:
        prefix = input("Enter the prefix for your files: ").strip()

    # Determine input file
    matching_files = glob.glob(f"{prefix}-sentence*.txt")
    if not matching_files:
        print(f"No transcript files found for prefix '{prefix}'. Exiting.")
        sys.exit(1)

    # Use the first match
    input_file = matching_files[0]
    output_file = f"{prefix}_fine_tune_data.jsonl"

    # Remove output file if it exists
    if os.path.exists(output_file):
        os.remove(output_file)

    print(f"Processing input file: {input_file}")
    print(f"Output will be written to: {output_file}\n")

    generate_fine_tune_jsonl(
        input_file,
        output_file,
        rolling_lines=3,
        rolling_chars=500,
        sliding_window=True
    )

    print("✅ Fine-tune JSONL generation completed.")
