import requests
import time
import mysql.connector
from datetime import datetime
from difflib import SequenceMatcher

# -----------------------------
# CONFIGURATION
# -----------------------------
API_KEY = ""
BASE_URL = "https://api.openai.com/v1/chat/completions"

FINE_TUNES = {
    "all": "ft:gpt-3.5-turbo-0125:personal::C4gbFqQA",
    "01": "ft:gpt-3.5-turbo-0125:personal::C5gBvDKJ"
}


short_prompts = {
    "Introduction": "Write an engaging introduction for beginners who want to start a YouTube channel...",
    "Chapter 1: Finding Your Why": "Create a section about helping beginners find their 'why'...",
    "Chapter 2: Choosing Your Topic and Research": "Write a chapter about choosing a YouTube channel topic...",
    "Chapter 3: Creating Your Channel": "Generate a detailed guide for beginners on creating their YouTube channel...",
    "Chapter 4: Video Creation Process": "Write a chapter about creating the first videos for a YouTube channel...",
    "Chapter 5: The Reward": "Create a chapter explaining the benefits and rewards of starting a YouTube channel...",
    "Conclusion": "Write a conclusion for a YouTube beginner guide..."
}

long_prompts = {
    "Introduction": (
        "Write an engaging introduction for beginners who want to start a YouTube channel. "
        "Show empathy by acknowledging common fears like not knowing what to name the channel or how to set it up. "
        "Use the Pain-Agitate-Solve technique to highlight struggles beginners face, then motivate the reader by promising a step-by-step walkthrough."
    ),
    "Chapter 1: Finding Your Why": (
        "Write about helping beginners find their 'why' for starting a YouTube channel. "
        "Use empathy by acknowledging fears like needing a logo or banner. "
        "Include social proof to normalize overthinking and motivational framing to encourage them to start now rather than waiting for perfection."
    ),
    "Chapter 2: Choosing Your Topic and Research": (
        "Write about choosing a YouTube channel topic and researching ideas. "
        "Provide step-by-step instructions for selecting a channel name and niche. "
        "Use the Pain-Agitate-Solve technique to address fears of overthinking and choosing the wrong name, then reassure that names can be changed later. "
        "Include motivational framing to encourage starting even without having everything figured out."
    ),
    "Chapter 3: Creating Your Channel": (
        "Generate a detailed guide for beginners on creating their YouTube channel. "
        "Include step-by-step instructions for setting up the banner, logo, and description. "
        "Show empathy for fears about sounding too polished. "
        "Use Pain-Agitate-Solve to address common setup problems and give actionable solutions. "
        "Add a lead magnet or free value hint, like promising a helpful tip or trick coming later."
    ),
    "Chapter 4: Video Creation Process": (
        "Talk about creating the first videos for a YouTube channel. "
        "Provide step-by-step instructions and motivate beginners by emphasizing that their first video just needs to be real. "
        "Include urgency to encourage starting immediately. "
        "Use Pain-Agitate-Solve to show that many people quit before uploading, and frame it to reduce fear and increase confidence."
    ),
    "Chapter 5: The Reward": (
        "Explaining the benefits and rewards of starting a YouTube channel. "
        "Include lead magnets like newsletters or free resources. "
        "Use social proof to show that following the steps leads to growth and momentum. "
        "Add motivational framing to emphasize that taking action builds confidence and long-term progress."
    ),
    "Conclusion": (
        "Write a conclusion for a YouTube beginner guide. "
        "Include a strong call-to-action, such as liking the video or commenting with their channel name. "
        "Use motivational framing to reinforce that YouTube is for everyone, not just big creators. "
        "Include empathy and relatability to encourage viewers to start small and show up consistently."
        "This is the final part so the last sentence should be saying bye for now to the viewer in thee last sentence."
    )
}

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "stixtricks"
}

YOUTUBE_TABLE = "youtube_scripts"
REFERENCE_TABLE = "reference_data"
FEEDBACK_TABLE = "feedback_data"

# -----------------------------
# DATABASE TABLE CREATION
# -----------------------------
def create_tables():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {YOUTUBE_TABLE} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        video_id VARCHAR(255),
        chapter_name VARCHAR(255),
        chapter_type ENUM('Short','Long') DEFAULT 'Short',
        content LONGTEXT,
        created_at DATETIME,
        prompt_tokens INT,
        completion_tokens INT,
        total_tokens INT
    )
    """)
    
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {REFERENCE_TABLE} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        chapter VARCHAR(255) UNIQUE,
        short_prompt LONGTEXT,
        long_prompt LONGTEXT
    )
    """)
    
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {FEEDBACK_TABLE} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        video_id VARCHAR(255),
        chapter VARCHAR(255),
        chapter_type ENUM('Short','Long'),
        generated_length INT,
        reference_length INT,
        length_diff INT,
        similarity FLOAT,
        reference_length_total INT,
        created_at DATETIME
    )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

# -----------------------------
# POPULATE REFERENCE DATA
# -----------------------------
def populate_reference_data():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    for chapter in short_prompts.keys():
        cursor.execute(f"""
            INSERT INTO {REFERENCE_TABLE} (chapter, short_prompt, long_prompt)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE short_prompt=%s, long_prompt=%s
        """, (chapter, short_prompts[chapter], long_prompts[chapter],
              short_prompts[chapter], long_prompts[chapter]))
    
    conn.commit()
    cursor.close()
    conn.close()
    print("[INFO] Reference data populated successfully.")

# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
def query_fine_tune(fine_tune_model, prompt):
    structured_prompt = (
        f"Please respond in three phases:\n"
        f"1) Plan: list bullet points of what you will cover.\n"
        f"2) Draft: write the full chapter content.\n"
        f"3) Final polish: rewrite for clarity and motivation.\n\n"
        f"Now write the chapter: {prompt}"
    )

    payload = {
        "model": fine_tune_model,
        "messages": [
            {"role": "system", "content": "You are a YouTube content coach helping creators in 2025."},
            {"role": "user", "content": structured_prompt}
        ],
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 900
    }

    try:
        response = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        usage = data.get("usage", {})
        return content, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), usage.get("total_tokens", 0)
    except requests.exceptions.RequestException as e:
        print("Error querying fine-tune:", e)
        return "[Error generating content]", 0, 0, 0

def insert_into_db(video_id, chapter, content, prompt_tokens, completion_tokens, total_tokens, chapter_type='Short'):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    sql = f"""
    INSERT INTO {YOUTUBE_TABLE} 
    (video_id, chapter_name, chapter_type, content, created_at, prompt_tokens, completion_tokens, total_tokens)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (video_id, chapter, chapter_type, content, datetime.now(), prompt_tokens, completion_tokens, total_tokens))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"[INFO] Inserted chapter '{chapter}' ({chapter_type}) into database.")

def calculate_similarity(text1, text2):
    return SequenceMatcher(None, text1, text2).ratio()

# -----------------------------
# FEEDBACK COMPARISON
# -----------------------------
def compare_and_store_feedback(video_id):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT chapter_name, chapter_type, content FROM {YOUTUBE_TABLE} WHERE video_id = %s", (video_id,))
    generated_rows = cursor.fetchall()
    
    cursor.execute(f"SELECT chapter, short_prompt, long_prompt FROM {REFERENCE_TABLE}")
    reference_rows = cursor.fetchall()
    
    feedback_list = []

    for g_chap, g_type, g_text in generated_rows:
        base_chap = g_chap.replace(" (Short)", "").replace(" (Long)", "")
        for r_chap, short_text, long_text in reference_rows:
            if base_chap == r_chap:
                ref_text = short_text if g_type == "Short" else long_text
                gen_len = len(g_text)
                ref_len = len(ref_text)
                similarity = calculate_similarity(g_text, ref_text)
                length_diff = abs(gen_len - ref_len)
                
                feedback_list.append((
                    video_id, base_chap, g_type, gen_len, ref_len, length_diff, similarity, ref_len, datetime.now()
                ))
    
    if feedback_list:
        sql = f"""
        INSERT INTO {FEEDBACK_TABLE} 
        (video_id, chapter, chapter_type, generated_length, reference_length, length_diff, similarity, reference_length_total, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(sql, feedback_list)
        conn.commit()
        print(f"[INFO] Stored {len(feedback_list)} feedback records.")
    
    cursor.close()
    conn.close()

# -----------------------------
# MAIN SCRIPT
# -----------------------------
def generate_script(fine_tune_key, video_id):
    if fine_tune_key not in FINE_TUNES:
        print("Invalid fine-tune key. Available keys:", list(FINE_TUNES.keys()))
        return

    model_id = FINE_TUNES[fine_tune_key]
    print(f"[INFO] Generating script using fine-tune '{fine_tune_key}' ({model_id})...\n")

    # Generate short-form chapters
    for chapter, prompt in short_prompts.items():
        content, prompt_tokens, completion_tokens, total_tokens = query_fine_tune(model_id, prompt)
        insert_into_db(video_id, chapter, content, prompt_tokens, completion_tokens, total_tokens, chapter_type='Short')
        time.sleep(1)

    # Generate long-form chapters
    for chapter, prompt in long_prompts.items():
        content, prompt_tokens, completion_tokens, total_tokens = query_fine_tune(model_id, prompt)
        insert_into_db(video_id, chapter, content, prompt_tokens, completion_tokens, total_tokens, chapter_type='Long')
        time.sleep(1)
    
    # Compare feedback
    compare_and_store_feedback(video_id)

# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    create_tables()
    populate_reference_data()
    video_id = input("Enter video ID: ").strip()
    print("Available personalities:", list(FINE_TUNES.keys()))
    choice = input("Enter personality key: ").strip().lower()
    generate_script(choice, video_id)
    print("\n[INFO] All chapters generated, inserted, and feedback recorded.")
