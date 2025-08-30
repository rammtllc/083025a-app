import sys
import os
import json
import pygame
import numpy as np
import sys
import os
import json
import pygame
import numpy as np
import cv2
from pygame._sdl2.video import Window, Texture, Renderer, Image


# ----------------------------
# Base directories (all relative to this file)
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "media")
UTILS_DIR = os.path.join(BASE_DIR, "utils")
JSON_DIR = os.path.join(UTILS_DIR, "json")

# ----------------------------
# Create folders if missing
# ----------------------------
for folder in [MEDIA_DIR, UTILS_DIR, JSON_DIR]:
    os.makedirs(folder, exist_ok=True)

# Ensure utils folder is recognized as a package
init_file = os.path.join(UTILS_DIR, "__init__.py")
if not os.path.exists(init_file):
    with open(init_file, "w") as f:
        f.write("# utils package\n")

# ----------------------------
# Default settings
# ----------------------------
DEFAULT_SETTINGS_CONTENT = {
    "font_name": os.path.join(MEDIA_DIR, "LuckiestGuy-Regular.ttf"),
    "font_size": 24,
    "show_timestamp": True,
    "record_video": False,
    "timestamp_mode": "word",
    "timestamps_file_word": os.path.join(MEDIA_DIR, "shorts-transcript_by_word.txt"),
    "timestamps_file_sentence": os.path.join(MEDIA_DIR, "shorts-transcript_by_sentence.txt"),
    "event_schedule_path": os.path.join(MEDIA_DIR, "event_schedule.json"),
    "voiceover_path": os.path.join(MEDIA_DIR, "voiceover.mp3")
}
DEFAULT_SETTINGS_PATH = os.path.join(JSON_DIR, "default_settings.json")

# ----------------------------
# Create dummy files
# ----------------------------
def create_dummy_files():
    # Font
    if not os.path.exists(DEFAULT_SETTINGS_CONTENT["font_name"]):
        with open(DEFAULT_SETTINGS_CONTENT["font_name"], "wb") as f:
            f.write(b"")

    # Word transcript with zero-padded timestamps
    if not os.path.exists(DEFAULT_SETTINGS_CONTENT["timestamps_file_word"]):
        words = ["Hello", "world", "this", "is", "a", "dummy", "timestamp", "file"]
        with open(DEFAULT_SETTINGS_CONTENT["timestamps_file_word"], "w") as f:
            for i, word in enumerate(words):
                f.write(f"{i:03d} {word}\n")

    # Sentence transcript with zero-padded timestamps
    if not os.path.exists(DEFAULT_SETTINGS_CONTENT["timestamps_file_sentence"]):
        sentences = [
            "Hello world.",
            "This is a dummy sentence file.",
            "Enjoy testing!"
        ]
        with open(DEFAULT_SETTINGS_CONTENT["timestamps_file_sentence"], "w") as f:
            for i, sentence in enumerate(sentences):
                f.write(f"{i:03d} {sentence}\n")

    # Event schedule
    if not os.path.exists(DEFAULT_SETTINGS_CONTENT["event_schedule_path"]):
        schedule = {
            "events": [
                {"time": 0, "action": "start"},
                {"time": 5, "action": "middle"},
                {"time": 10, "action": "end"}
            ]
        }
        with open(DEFAULT_SETTINGS_CONTENT["event_schedule_path"], "w") as f:
            json.dump(schedule, f, indent=2)

    # Voiceover
    if not os.path.exists(DEFAULT_SETTINGS_CONTENT["voiceover_path"]):
        try:
            from pydub import AudioSegment
            silent = AudioSegment.silent(duration=1000)
            silent.export(DEFAULT_SETTINGS_CONTENT["voiceover_path"], format="mp3")
        except ImportError:
            with open(DEFAULT_SETTINGS_CONTENT["voiceover_path"], "wb") as f:
                f.write(b"")

    # Utils dummy files
    files_content = {
        "visuals.py": (
            "def run_visuals(timestamps, event_schedule, font_name, font_size, settings, data=None):\n"
            "    print('Running visuals...')\n"
        ),
        "video_audio.py": (
            "def load_timestamps(path):\n"
            "    try:\n"
            "        with open(path,'r') as f:\n"
            "            return [line.strip() for line in f if line.strip()]\n"
            "    except:\n"
            "        return []\n"
        ),
        "utils_menu.py": (
            "def start_screen(screen, width, height, settings):\n"
            "    print('Displaying start screen...')\n"
            "    return settings\n"
        ),
        "constants.py": (
            "WIDTH = 800\n"
            "HEIGHT = 600\n"
            "FONT_SIZE = 24\n"
        )
    }
    for fname, content in files_content.items():
        path = os.path.join(UTILS_DIR, fname)
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(content)

    # Default settings JSON
    if not os.path.exists(DEFAULT_SETTINGS_PATH) or os.path.getsize(DEFAULT_SETTINGS_PATH) == 0:
        with open(DEFAULT_SETTINGS_PATH, "w") as f:
            json.dump(DEFAULT_SETTINGS_CONTENT, f, indent=2)

# Ensure all dummy files exist before importing anything from utils
create_dummy_files()

# ----------------------------
# Add project root to module search path
# ----------------------------
sys.path.insert(0, BASE_DIR)

# --- Utils imports ---
from utils.visuals import run_visuals
from utils.video_audio import load_timestamps
from utils.utils_menu import start_screen
from utils.constants import WIDTH, HEIGHT, FONT_SIZE

# ----------------------------
# Helpers
# ----------------------------
def load_json(path, fallback=None):
    try:
        with open(path, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return fallback if fallback is not None else {}
            return data
    except Exception:
        return fallback if fallback is not None else {}

def save_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Could not save {path}: {e}")

def resolve_path(base, path, default):
    val = path if path else default
    return os.path.join(base, val) if not os.path.isabs(val) else val

def load_timestamps_file(settings):
    mode = settings.get("timestamp_mode", "word")
    path = settings.get("timestamps_file_word") if mode=="word" else settings.get("timestamps_file_sentence")
    path = resolve_path(BASE_DIR, path, "")
    if not os.path.exists(path):
        raise RuntimeError(f"Timestamps file missing: {path}")
    return path

# ----------------------------
# Parse timestamp file (0.000 format)
# ----------------------------
def parse_timestamps_file(path):
    """
    Converts lines like '0.000 Hello' into a list of {"time": float, "text": str}.
    """
    out = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                continue
            time_str, text = parts
            try:
                out.append({"time": float(time_str), "text": text})
            except ValueError:
                continue
    return out


# ----------------------------
# Video helpers
# ----------------------------
def play_video_setup(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video: {video_path}")
        return None, None
    video_window = Window("Video Player", size=(640, 360), position=(850, 50))
    renderer = Renderer(video_window)
    return cap, renderer

def draw_video_frame(cap, renderer):
    ret, frame = cap.read()
    if not ret:
        return False  # end of video
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.resize(frame, (640, 360))
    surf = pygame.surfarray.make_surface(np.transpose(frame, (1, 0, 2)))
    tex = Texture.from_surface(renderer, surf)
    renderer.clear()
    renderer.copy(tex)
    renderer.present()
    return True

# ----------------------------
# Main program
# ----------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("YouTube Video Maker")

    # --- set up video window ---
    video_path = os.path.join(MEDIA_DIR, "demo.mp4")
    cap = None
    video_surf = None
    if os.path.exists(video_path):
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            video_surf = pygame.Surface((WIDTH // 2, HEIGHT))  # right side
        else:
            print(f"[ERROR] Could not open video: {video_path}")
            cap = None

    clock = pygame.time.Clock()
    running = True

    # --- preload settings and data once ---
    settings = load_json(DEFAULT_SETTINGS_PATH, DEFAULT_SETTINGS_CONTENT)
    for key in ["font_name","timestamps_file_word","timestamps_file_sentence","event_schedule_path","voiceover_path"]:
        settings[key] = resolve_path(BASE_DIR, settings.get(key), DEFAULT_SETTINGS_CONTENT[key])

    if not os.path.exists(settings["event_schedule_path"]):
        create_dummy_files()

    timestamps_file = load_timestamps_file(settings)
    timestamps = parse_timestamps_file(timestamps_file)

    data = load_json(settings["event_schedule_path"], {})
    event_schedule = data.get("events", [])

    # Start screen once
    settings = start_screen(screen, WIDTH, HEIGHT, settings)
    save_json(DEFAULT_SETTINGS_PATH, settings)

    # --- main loop: update visuals + video together ---
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # run one step of visuals
        run_visuals(
            timestamps,
            event_schedule,
            settings.get("font_name"),
            settings.get("font_size", FONT_SIZE),
            settings,
            data=data,
            screen=screen
        )

        # --- RIGHT: video frame ---
        if cap and video_surf:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (WIDTH // 2, HEIGHT))
                pygame.surfarray.blit_array(video_surf, frame_resized.swapaxes(0, 1))
                screen.blit(video_surf, (WIDTH // 2, 0))

        pygame.display.flip()
        clock.tick(30)

    if cap:
        cap.release()


if __name__ == "__main__":
    main()
