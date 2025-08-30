import os
import json
import mysql.connector
from mysql.connector import Error
from openai import OpenAI
import time
import random
import sys

client = OpenAI()

# -----------------------------
# Database Setup
# -----------------------------
def get_connection():
    return mysql.connector.connect(
        host="localhost",      # change if needed
        user="root",           # change
        password="",           # change
        database="youtube_data"  # change
    )

# -----------------------------
# Moderation Check with Batching & Dynamic Backoff
# -----------------------------
#def check_texts(msgs, retries=5):
#    for attempt in range(retries):
#        try:
#            response = client.moderations.create(
#                model="omni-moderation-latest",
#                input=msgs
#            )
#            return response.results, None
#        except Exception as e:
#            if "429" in str(e):
#                wait_time = (2 ** attempt) + random.random()
#                print(f"⚠️ Rate limit hit. Sleeping {wait_time:.2f}s...")
#                time.sleep(wait_time)
#                continue
#            return None, str(e)
#    return None, f"Failed after {retries} retries"

# -----------------------------
# Moderation Check with Hardcoded Delay
# -----------------------------
HARD_DELAY_SECONDS = 2  # <-- Change this to adjust the delay

def check_texts(msgs):
    results = []
    for msg in msgs:
        try:
            response = client.moderations.create(
                model="omni-moderation-latest",
                input=msg
            )
            results.append(response.results[0])
            print(f"✅ Moderation call done. Waiting {HARD_DELAY_SECONDS}s before next call...")
            time.sleep(HARD_DELAY_SECONDS)  # Hardcoded delay
        except Exception as e:
            print(f"❌ Moderation error: {e}")
            results.append({"flagged": True, "categories": None})
            time.sleep(HARD_DELAY_SECONDS)  # Still wait even if error
    return results, None

# -----------------------------
# Database Setup
# -----------------------------
def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dataset_lines (
            id INT AUTO_INCREMENT PRIMARY KEY,
            file_name VARCHAR(255),
            line_number INT,
            content JSON,
            status ENUM('good','bad','error') NOT NULL,
            categories JSON,
            error_msg TEXT,
            UNIQUE KEY unique_file_line (file_name, line_number)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()


# -----------------------------
# Insert / Update Line (file-specific)
# -----------------------------
def insert_line(file_name, line_number, data, status, categories=None, error=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO dataset_lines (file_name, line_number, content, status, categories, error_msg)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            content=VALUES(content),
            status=VALUES(status),
            categories=VALUES(categories),
            error_msg=VALUES(error_msg)
    """, (
        file_name,
        line_number,
        json.dumps(data),
        status,
        json.dumps(categories) if categories else None,
        error
    ))
    conn.commit()
    cursor.close()
    conn.close()


# -----------------------------
# Check if already good (file-specific)
# -----------------------------
def already_good(file_name, line_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status FROM dataset_lines
        WHERE file_name=%s AND line_number=%s
    """, (file_name, line_number))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row is not None and row[0] == "good"


# -----------------------------
# Process lines in a file and return if any line was bad
# -----------------------------
# -----------------------------
# Process lines in a file and return if any line was bad
# -----------------------------
def process_jsonl_file(file_path, batch_size=10):
    file_name = os.path.basename(file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        all_lines = list(f)
    total_lines = len(all_lines)

    file_has_bad_line = False

    for batch_start in range(0, total_lines, batch_size):
        batch_lines = all_lines[batch_start:batch_start + batch_size]
        batch_data = []
        line_numbers = []
        flagged_lines = {}

        for idx, line in enumerate(batch_lines):
            ln = batch_start + idx + 1
            if already_good(file_name, ln):
                print(f"[{ln}/{total_lines}] ✅ Skipping line {ln}, already marked good.")
                continue
            try:
                data = json.loads(line)
                batch_data.append(data)
                line_numbers.append(ln)
            except Exception as e:
                insert_line(file_name, ln, line.strip(), "error", None, str(e))
                print(f"[{ln}/{total_lines}] ❌ Parse error: {e}")
                file_has_bad_line = True

        if not batch_data:
            continue

        messages_flat = []
        msg_map = []
        for i, data in enumerate(batch_data):
            msgs = [m["content"] for m in data.get("messages", [])]
            for m in msgs:
                messages_flat.append(m)
                msg_map.append(i)

        results, error = check_texts(messages_flat)
        if error:
            for ln, data in zip(line_numbers, batch_data):
                insert_line(file_name, ln, data, "error", None, error)
                print(f"[{ln}/{total_lines}] ❌ Error: {error}")
            file_has_bad_line = True
            continue

        for msg_idx, res in enumerate(results):
            if res.flagged:
                ln_idx = msg_map[msg_idx]
                flagged_lines[line_numbers[ln_idx]] = res.categories.to_dict() if res.categories else None

        for ln, data in zip(line_numbers, batch_data):
            if ln in flagged_lines:
                insert_line(file_name, ln, data, "bad", flagged_lines[ln], None)
                print(f"[{ln}/{total_lines}] ⚠️ Flagged as bad")
                file_has_bad_line = True
            else:
                insert_line(file_name, ln, data, "good", None, None)
                print(f"[{ln}/{total_lines}] [OK] Inserted as good")

    return file_has_bad_line, all_lines


# -----------------------------
# Aggregate all JSONL files in folder with delay between files
# -----------------------------
def aggregate_jsonl_folder():
    folder = "jsonl"
    good_file = "fine_tune_data_good.jsonl"
    bad_file = "fine_tune_data_bad.jsonl"

    # Ensure files exist
    open(good_file, 'a', encoding='utf-8').close()
    open(bad_file, 'a', encoding='utf-8').close()

    # Build static list of files to process
    files_to_process = [
        f for f in os.listdir(folder)
        if f.endswith(".jsonl") and f not in (good_file, bad_file)
    ]

    for filename in files_to_process:
        filepath = os.path.join(folder, filename)
        print(f"\nProcessing file: {filename}")

        has_bad, all_lines = process_jsonl_file(filepath)
        target_file = bad_file if has_bad else good_file

        # Append file content to the appropriate aggregate file
        with open(target_file, "a", encoding="utf-8") as f:
            f.writelines(all_lines)

        os.remove(filepath)
        print(f"Moved {filename} → {'bad' if has_bad else 'good'} and deleted original.")

        # Wait 60 seconds before processing the next file
        print("⏱ Waiting 60 seconds before next file...")
        time.sleep(60)
# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    create_table()

    if len(sys.argv) > 1 and sys.argv[1] == "--retry-bad-only":
        retry_bad_or_error()
    else:
        aggregate_jsonl_folder()
