from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

def scroll_until_all_videos_loaded(driver, pause=1):
    last_count = 0
    while True:
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(pause)
        videos = driver.find_elements("id", "video-title")
        if len(videos) == last_count:
            break
        last_count = len(videos)
    return driver.find_elements("id", "video-title")

def parse_date_from_text(text):
    match = re.match(r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", text)
    if not match:
        return None
    num, unit = int(match[1]), match[2]
    now = datetime.now()
    kwargs = {}
    if unit == "second": kwargs["seconds"] = num
    elif unit == "minute": kwargs["minutes"] = num
    elif unit == "hour": kwargs["hours"] = num
    elif unit == "day": kwargs["days"] = num
    elif unit == "week": kwargs["weeks"] = num
    elif unit == "month": kwargs["months"] = num
    elif unit == "year": kwargs["years"] = num
    return now - relativedelta(**kwargs)

def check_ads_on_latest_video(driver, videos):
    if not videos: return False
    latest_video_url = videos[0].get_attribute("href")
    if not latest_video_url: return False
    driver.get(latest_video_url)
    time.sleep(3)
    ad_elements = driver.find_elements("xpath", "//ytd-ad-slot-renderer | //button[contains(text(),'Skip Ad')]")
    return len(ad_elements) > 0

def analyze_channel(channel_handle):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # --- Channel main page ---
        driver.get(f"https://www.youtube.com/@{channel_handle}")
        time.sleep(5)

        page_text = driver.execute_script("return document.body.innerText;")
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]

        handle_line_idx = next((i for i, l in enumerate(lines) if l.startswith("@")), -1)
        if handle_line_idx == -1:
            print("Could not find channel handle")
            return

        channel_name = lines[handle_line_idx - 1] if handle_line_idx > 0 else "Unknown"
        handle = lines[handle_line_idx]
        subscribers_text = next((l for l in lines[handle_line_idx+1:handle_line_idx+5] if "subscribers" in l), "0 subscribers")
        video_count = next((l for l in lines[handle_line_idx+1:handle_line_idx+5] if re.match(r"\d+ videos", l)), "Unknown")
        description_idx = max([i for i, l in enumerate(lines) if l == subscribers_text or l == video_count] + [handle_line_idx])
        description = lines[description_idx + 1] if description_idx + 1 < len(lines) else "Unknown"

        # --- Estimate subscriber count number ---
        subscribers_number = 0
        subs_match = re.match(r"([\d,.]+)K?M?", subscribers_text.replace(",", ""))
        if subs_match:
            subs_val = subs_match[1]
            if "M" in subscribers_text:
                subscribers_number = float(subs_val) * 1_000_000
            elif "K" in subscribers_text:
                subscribers_number = float(subs_val) * 1_000
            else:
                subscribers_number = float(subs_val)

        # --- Videos page ---
        driver.get(f"https://www.youtube.com/@{channel_handle}/videos")
        time.sleep(3)

        videos = scroll_until_all_videos_loaded(driver, pause=1)
        oldest_video_date_text = None

        if videos:
            last_video = videos[-1]
            parent = last_video.find_element("xpath", "./ancestor::ytd-rich-item-renderer")
            spans = parent.find_elements("xpath", ".//span[contains(@class,'style-scope ytd-video-meta-block')]")
            if len(spans) >= 2:
                oldest_video_date_text = spans[1].text

        # Estimate channel age
        channel_age_years = 0
        if oldest_video_date_text:
            dt = parse_date_from_text(oldest_video_date_text)
            if dt:
                delta = relativedelta(datetime.now(), dt)
                channel_age_years = delta.years
                channel_age_text = f"{delta.years} years, {delta.months} months"
            else:
                channel_age_text = "Unknown"
        else:
            channel_age_text = "Unknown"

        # --- Monetization check ---
        meets_minimum = subscribers_number >= 1000 and channel_age_years >= 1

        # --- Heuristic ads check ---
        ads_detected = check_ads_on_latest_video(driver, videos)
        if ads_detected:
            monetization_status = "Likely monetized"
        else:
            monetization_status = "Maybe not monetized" if not meets_minimum else "Meets minimum requirements"

        print("=== CHANNEL INFO ===")
        print(f"Channel Name: {channel_name}")
        print(f"Handle: {handle}")
        print(f"Subscribers: {subscribers_text}")
        print(f"Video count: {video_count}")
        print(f"Description: {description}")
        print("=== OLDEST VIDEO INFO ===")
        print(f"Upload date text: {oldest_video_date_text}")
        print(f"Estimated channel age: {channel_age_text}")
        print("=== MONETIZATION CHECK ===")
        print(f"Minimum check: {'Yes' if meets_minimum else 'No'}")
        print(f"Heuristic ads check: {monetization_status}")

    finally:
        driver.quit()

if __name__ == "__main__":
    channel_handle = input("Enter the YouTube channel handle (without @): ").strip()
    analyze_channel(channel_handle)
