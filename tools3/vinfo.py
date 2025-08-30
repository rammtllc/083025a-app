import os
import sys
import time
import re
import hashlib
import io
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pytesseract
from shutil import which
import Levenshtein  # for fuzzy string matching
import mysql.connector  # <--- added

# ----------------- DB CONFIG -----------------
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "youtube_data",
    "table": "youtube_vids"
}



# ----------------- DATABASE INSERT -----------------
def insert_results_into_db(results, db_config):
    try:
        conn = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )
        cursor = conn.cursor()

        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {db_config['table']} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title TEXT,
                url TEXT,
                score FLOAT,
                ocr_path TEXT,
                ocr_views TEXT
            )
        """)

        insert_query = f"""
            INSERT INTO {db_config['table']} (title, url, score, ocr_path, ocr_views)
            VALUES (%s, %s, %s, %s, %s)
        """

        for video in results:
            try:
                cursor.execute(insert_query, (
                    video.get("title"),
                    video.get("url"),
                    video.get("score"),
                    video.get("ocr_path"),
                    video.get("views")
                ))
            except mysql.connector.Error as e:
                print(f"Error inserting {video.get('title')}: {e}")

        conn.commit()
        print(f"Inserted {len(results)} records into {db_config['table']}")
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()


# ----------------- TESSERACT AUTO-DETECT -----------------
def find_tesseract():
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]
    for path in possible_paths:
        if os.path.isfile(path):
            return path
    tesseract_path = which("tesseract")
    if tesseract_path:
        return tesseract_path
    return None

tesseract_cmd = find_tesseract()
if not tesseract_cmd:
    print("Error: Tesseract executable not found. Install it and add to PATH.")
    sys.exit(1)
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
print(f"Using Tesseract at: {tesseract_cmd}")


# ----------------- HELPER FUNCTIONS -----------------
def screenshot_hash(img):
    return hashlib.md5(img.tobytes()).hexdigest()


# ----------------- SELENIUM SCROLL & CAPTURE -----------------
def scroll_and_capture(channel_handle, screenshot_folder="screenshots", scroll_pause=2):
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    os.makedirs(screenshot_folder, exist_ok=True)

    try:
        driver.get(f"https://www.youtube.com/@{channel_handle}/videos")
        time.sleep(3)

        last_hash = None
        scroll_index = 1

        while True:
            png = driver.get_screenshot_as_png()
            full_img = Image.open(io.BytesIO(png))

            screenshot_path = os.path.join(screenshot_folder, f"scroll_{scroll_index}.png")
            full_img.save(screenshot_path)
            print(f"Saved screenshot: {screenshot_path}")
            scroll_index += 1

            curr_hash = screenshot_hash(full_img)
            if last_hash == curr_hash:
                print("No new content loaded, stopping scroll.")
                break
            last_hash = curr_hash

            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(scroll_pause)
    finally:
        driver.quit()


# ----------------- EXTRACT TITLES & VIEWS -----------------
def extract_titles_and_views_from_image(img, save_folder="titles_clips", base_name="screenshot"):
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)
    os.makedirs(save_folder, exist_ok=True)

    clips_info = []
    saved_count = 0
    img_width, img_height = img.size

    for i, text in enumerate(data['text']):
        if len(text.strip()) > 3:
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

            # safely expand title box within image bounds
            left = max(x - 50, 0)
            top = max(y - 10, 0)
            right = min(x + w + 50, img_width - 1)
            bottom = min(y + h + 10, img_height - 1)

            cropped = img.crop((left, top, right, bottom))
            saved_count += 1
            clip_path = os.path.join(save_folder, f"{base_name}_title_{saved_count}.png")
            cropped.save(clip_path)

            title_text = pytesseract.image_to_string(cropped, config=custom_config).strip()

            # approximate view count area below title
            view_top = bottom
            view_bottom = min(bottom + 40, img_height - 1)
            if view_bottom > view_top:
                view_crop = img.crop((left, view_top, right, view_bottom))
                view_text = pytesseract.image_to_string(view_crop, config=custom_config).strip()
            else:
                view_text = ""

            if title_text:
                clips_info.append({
                    "path": clip_path,
                    "text": title_text,
                    "views": view_text
                })

    return clips_info


# ----------------- PARSE VIDEOS FROM SCREENSHOTS -----------------
def parse_videos_from_screenshots(screenshot_folder="screenshots"):
    all_clips = []
    seen_texts = set()

    for idx, file_name in enumerate(sorted(os.listdir(screenshot_folder)), start=1):
        if not file_name.lower().endswith((".png", ".jpg")):
            continue
        path = os.path.join(screenshot_folder, file_name)
        img = Image.open(path)
        clips = extract_titles_and_views_from_image(img, save_folder="titles_clips", base_name=f"scroll_{idx}")

        for clip in clips:
            clean_text = clip["text"].strip().lower()
            if clean_text not in seen_texts:
                all_clips.append(clip)
                seen_texts.add(clean_text)

    print(f"\nExtracted {len(all_clips)} unique OCR titles and views from screenshots.\n")
    return all_clips


# ----------------- MATCH OCR TITLES TO LINKS -----------------
def get_links_by_title(channel_handle, clips_info, db_config=None):
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(f"https://www.youtube.com/@{channel_handle}/videos")
    time.sleep(3)

    anchor_elements = driver.find_elements("xpath", '//a[contains(@href, "watch?")]')
    watch_links = []
    for a in anchor_elements:
        href = a.get_attribute("href")
        title = a.get_attribute("title") or a.text
        if href and title:
            watch_links.append({"title": title.strip(), "url": href.strip()})

    results = []
    seen_urls = set()

    for clip in clips_info:
        clip_text_clean = re.sub(r'\W+', ' ', clip["text"]).strip().lower()
        best_match = None
        best_score = 0

        for link in watch_links:
            title_clean = re.sub(r'\W+', ' ', link["title"]).strip().lower()
            score = Levenshtein.ratio(clip_text_clean, title_clean)
            if score > best_score:
                best_score = score
                best_match = {
                    "title": link["title"],
                    "url": link["url"],
                    "score": score,
                    "ocr_path": clip["path"],
                    "views": clip.get("views")
                }

        if best_match and best_match["url"] not in seen_urls:
            results.append(best_match)
            seen_urls.add(best_match["url"])

    results = sorted(results, key=lambda x: x["score"], reverse=True)

    for i, video in enumerate(results, start=1):
        print(f"{i}. Score: {video['score']:.2f}, Title: {video['title']}, Views: {video['views']}")
        print(f"   URL: {video['url']}\n")

    if db_config:
        insert_results_into_db(results, db_config)

    driver.quit()

# --- Separate function to just display OCR results from screenshots ---
def show_ocr_from_screenshots(screenshot_folder="screenshots"):
    custom_config = r'--oem 3 --psm 6'
    for idx, file_name in enumerate(sorted(os.listdir(screenshot_folder)), start=1):
        if not file_name.lower().endswith((".png", ".jpg")):
            continue
        path = os.path.join(screenshot_folder, file_name)
        img = Image.open(path)

        data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)
        print(f"\n=== OCR results from screenshot: {file_name} ===")
        for i, text in enumerate(data['text']):
            if text.strip():
                print(f"- Text: '{text.strip()}' at ({data['left'][i]}, {data['top'][i]}, "
                      f"{data['width'][i]}, {data['height'][i]})")


def parse_views(views_text):
    match = re.search(r"([\d,.]+)\s*([KM]?) views", views_text.replace(",", ""))
    if match:
        num, suffix = match.groups()
        num = float(num)
        if suffix.upper() == "M":
            return int(num * 1_000_000)
        elif suffix.upper() == "K":
            return int(num * 1_000)
        else:
            return int(num)
    return 0

# --- Separate function to extract and save 'views'-focused screenshots ---
def save_views_clips_from_screenshots(screenshot_folder="screenshots", save_folder="views_clips", db_config=None):
    custom_config = r'--oem 3 --psm 6'
    os.makedirs(save_folder, exist_ok=True)
    
    all_clips_info = []
    
    for idx, file_name in enumerate(sorted(os.listdir(screenshot_folder)), start=1):
        if not file_name.lower().endswith((".png", ".jpg")):
            continue
        path = os.path.join(screenshot_folder, file_name)
        img = Image.open(path)
        
        data = pytesseract.image_to_data(img, config=custom_config, output_type=pytesseract.Output.DICT)
        saved_count = 0
        
        for i, text in enumerate(data['text']):
            if 'views' in text.lower():
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                
                # Expand area around 'views'
                left = max(x - 100, 0)
                top = max(y - 300, 0)
                right = min(x + 300, img.width)
                bottom = min(y + h + 10, img.height)
                
                cropped = img.crop((left, top, right, bottom))
                saved_count += 1
                clip_path = os.path.join(save_folder, f"scroll_{idx}_views_{saved_count}.png")
                cropped.save(clip_path)
                
                views_text = pytesseract.image_to_string(cropped, config=custom_config).strip()
                count = parse_views(views_text)
                
                print(f"Saved views clip: {clip_path}, Detected views: {count}, Coords: ({x},{y},{w},{h})")
                
                clip_info = {
                    "screenshot": file_name,
                    "path": clip_path,
                    "text": views_text,
                    "views": count,
                    "coords": {"x": x, "y": y, "w": w, "h": h}
                }
                all_clips_info.append(clip_info)
                
                # Insert into DB if db_config provided
                if db_config:
                    insert_views_clip_into_db(clip_info, db_config)
    
    print(f"\nTotal 'views'-focused clips saved: {len(all_clips_info)}\n")
    return all_clips_info


# --- Insert single views clip into MySQL ---
def insert_views_clip_into_db(clip_info, db_config):
    import mysql.connector
    try:
        conn = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )
        cursor = conn.cursor()
        # Create table if it doesn't exist
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS views_clips (
                id INT AUTO_INCREMENT PRIMARY KEY,
                screenshot VARCHAR(255),
                ocr_path TEXT,
                ocr_text TEXT,
                views INT,
                coord_x INT,
                coord_y INT,
                coord_w INT,
                coord_h INT
            )
        """)
        insert_query = f"""
            INSERT INTO views_clips 
            (screenshot, ocr_path, ocr_text, views, coord_x, coord_y, coord_w, coord_h)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            clip_info["screenshot"],
            clip_info["path"],
            clip_info["text"],
            clip_info["views"],
            clip_info["coords"]["x"],
            clip_info["coords"]["y"],
            clip_info["coords"]["w"],
            clip_info["coords"]["h"]
        ))
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Error inserting into DB: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

import mysql.connector
import Levenshtein
from collections import Counter

def generate_substrings(text, min_words=2):
    """
    Generate sliding window substrings from a text,
    including reversed substrings.
    """
    words = text.split()
    substrings = []
    for size in range(len(words), min_words - 1, -1):  # shrink window size
        for i in range(len(words) - size + 1):
            substr = " ".join(words[i:i+size])
            substrings.append(substr)

            # reversed substring
            substr_rev = " ".join(reversed(words[i:i+size]))
            substrings.append(substr_rev)

    return substrings


def update_youtube_views_from_views_clips(db_config, threshold=0.6):
    """
    Match YouTube titles to views clips using only unique substrings (2+ words).
    Prioritize longer unique substrings to avoid confusion between similar titles.
    Ensure no two videos get assigned the same views.
    """
    try:
        conn = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )
        cursor = conn.cursor(dictionary=True)

        # Fetch all YouTube video titles
        cursor.execute("SELECT id, title FROM youtube_vids")
        youtube_videos = cursor.fetchall()

        # Build substring frequency map across ALL titles
        all_substrings = []
        title_to_substrings = {}
        for video in youtube_videos:
            video_title_clean = video['title'].strip().lower()
            subs = generate_substrings(video_title_clean, min_words=2)
            title_to_substrings[video['id']] = subs
            all_substrings.extend(subs)

        substring_counts = Counter(all_substrings)

        # Keep only substrings that appear *once total*
        unique_substrings_map = {
            vid_id: [s for s in subs if substring_counts[s] == 1]
            for vid_id, subs in title_to_substrings.items()
        }

        # Sort substrings by length (descending) so longer unique phrases get checked first
        for vid_id, subs in unique_substrings_map.items():
            unique_substrings_map[vid_id] = sorted(subs, key=lambda s: len(s.split()), reverse=True)

        # Fetch all views clips
        cursor.execute("SELECT id, ocr_text, views FROM views_clips")
        views_clips = cursor.fetchall()

        assigned_views = set()  # track already used views counts

        for video in youtube_videos:
            video_title_clean = video['title'].strip().lower()
            best_match = None
            best_score = 0

            # Start with longest unique substrings (2+ words), fallback to 1 word if needed
            substrings = unique_substrings_map.get(video['id'], [])
            if not substrings:  # fallback
                substrings = generate_substrings(video_title_clean, min_words=1)

            for sub in substrings:
                for clip in views_clips:
                    clip_text_clean = clip['ocr_text'].strip().lower()
                    score = Levenshtein.ratio(sub, clip_text_clean)

                    # Candidate must be better *and* not duplicate an assigned view count
                    if score > best_score and clip['views'] not in assigned_views:
                        best_score = score
                        best_match = clip

                # stop early if confident and unique
                if best_score >= threshold and best_match:
                    break

            if best_match:
                assigned_views.add(best_match['views'])  # lock this views count

                update_query = """
                    UPDATE youtube_vids
                    SET ocr_views = %s
                    WHERE id = %s
                """
                cursor.execute(update_query, (best_match['views'], video['id']))

                if best_score >= threshold:
                    print(f"✅ Matched '{video['title']}' → views: {best_match['views']} (score={best_score:.2f})")
                else:
                    print(f"⚠️ Weak unique match for '{video['title']}' → views: {best_match['views']} (score={best_score:.2f})")
            else:
                print(f"❌ Could not find unique match for '{video['title']}'")

        conn.commit()
        print("\n🎯 Finished updating youtube_vids with unique non-duplicate matches.")

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()


import os
import shutil
import mysql.connector

# ----------------- CLEAN FOLDERS -----------------
def reset_folders(folders):
    for folder in folders:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"Deleted existing folder: {folder}")
        os.makedirs(folder, exist_ok=True)
        print(f"Created fresh folder: {folder}")

# ----------------- CLEAN DATABASE TABLES -----------------
def reset_db_tables(db_config, tables):
    try:
        conn = mysql.connector.connect(
            host=db_config["host"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )
        cursor = conn.cursor()
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"Dropped table if existed: {table}")
        conn.commit()
    except mysql.connector.Error as e:
        print(f"Database error while resetting tables: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

# ----------------- MAIN -----------------
if __name__ == "__main__":
# --- Call these at the very start ---
    folders_to_reset = ["screenshots", "titles_clips", "views_clips"]
    reset_folders(folders_to_reset)

    tables_to_reset = ["youtube_vids", "views_clips"]
    reset_db_tables(db_config, tables_to_reset)

    channel_handle = input("Enter the YouTube channel handle (without @): ").strip()

    print("\nScrolling and capturing screenshots...")
    scroll_and_capture(channel_handle, screenshot_folder="screenshots", scroll_pause=2)

    print("\nParsing screenshots and extracting OCR titles...")
    clips_info = parse_videos_from_screenshots("screenshots")

    print("\n--- Displaying OCR results from screenshots ---")
    show_ocr_from_screenshots("screenshots")  # <- This shows everything detected

    print("\nMatching OCR titles to closest YouTube video links and inserting into DB...")
    get_links_by_title(channel_handle, clips_info, db_config=db_config)

    print("\n--- Saving 'views'-focused clips from screenshots ---")
    views_clips_info = save_views_clips_from_screenshots("screenshots", save_folder="views_clips")

    views_clips_info = save_views_clips_from_screenshots(
    screenshot_folder="screenshots",
    save_folder="views_clips",
    db_config=db_config
    )
    update_youtube_views_from_views_clips(db_config)
