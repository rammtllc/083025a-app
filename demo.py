import os
import pygame
from pyvidplayer2 import Video
import json

# --- Default constants ---
WIDTH, HEIGHT = 1280, 720
FONT_SIZE = 24
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")
DEFAULT_SETTINGS_CONTENT = {
    "font_name": None,
    "timestamps_file_word": "timestamps_word.txt",
    "timestamps_file_sentence": "timestamps_sentence.txt",
    "event_schedule_path": "event_schedule.json",
    "voiceover_path": "voiceover.mp3",
    "font_size": FONT_SIZE
}

# --- Stub functions for missing dependencies ---
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def resolve_path(base_dir, path, default):
    return os.path.join(base_dir, path) if path else os.path.join(base_dir, default)

def create_dummy_files():
    print("[INFO] Creating dummy files...")

def load_timestamps_file(settings):
    return settings.get("timestamps_file_word")

def parse_timestamps_file(file_path):
    return []  # Return empty list for now

def start_screen(screen, width, height, settings):
    screen.fill((0, 0, 0))
    pygame.display.flip()
    pygame.time.wait(1000)
    return settings

def run_visuals(timestamps, event_schedule, font_name, font_size, settings, data=None, screen=None):
    screen.fill((50, 50, 50))
    font = pygame.font.SysFont(font_name, font_size)
    text = font.render("Visuals Here", True, (255, 255, 255))
    screen.blit(text, (50, 50))

# --- Main function ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("YouTube Video Maker")
    clock = pygame.time.Clock()

    # --- load settings ---
    settings = load_json(DEFAULT_SETTINGS_PATH, DEFAULT_SETTINGS_CONTENT)
    for key in ["font_name", "timestamps_file_word", "timestamps_file_sentence", "event_schedule_path", "voiceover_path"]:
        settings[key] = resolve_path(BASE_DIR, settings.get(key), DEFAULT_SETTINGS_CONTENT.get(key, ""))

    if not os.path.exists(settings["event_schedule_path"]):
        create_dummy_files()

    timestamps_file = load_timestamps_file(settings)
    timestamps = parse_timestamps_file(timestamps_file)
    data = load_json(settings["event_schedule_path"], {})
    event_schedule = data.get("events", [])

    # Start screen once
    settings = start_screen(screen, WIDTH, HEIGHT, settings)
    save_json(DEFAULT_SETTINGS_PATH, settings)

    # --- set up video via PyVidPlayer2 ---
    video_path = os.path.join(BASE_DIR, "demo.mp4")  # Look for demo.mp4 in the same directory
    if not os.path.exists(video_path):
        print(f"[ERROR] Video not found: {video_path}")
        return

    vid = Video(video_path)

    # Wait until first frame is loaded
    for _ in range(10):
        vid.update()
        if vid.frame:
            break
    if not vid.frame:
        print(f"[ERROR] Could not load video frame: {video_path}")
        return

    # Video sizing
    vid_width, vid_height = vid.frame.get_width(), vid.frame.get_height()
    video_aspect = vid_width / vid_height

    video_target_width = WIDTH // 2
    video_target_height = HEIGHT
    window_aspect = video_target_width / video_target_height

    if video_aspect > window_aspect:
        scale_width = video_target_width
        scale_height = int(video_target_width / video_aspect)
    else:
        scale_height = video_target_height
        scale_width = int(video_target_height * video_aspect)

    x_offset = WIDTH - scale_width
    y_offset = (HEIGHT - scale_height) // 2

    # Temporary surface for video
    temp_surface = pygame.Surface((scale_width, scale_height))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- update visuals on left half ---
        run_visuals(
            timestamps,
            event_schedule,
            settings.get("font_name"),
            settings.get("font_size", FONT_SIZE),
            settings,
            data=data,
            screen=screen
        )

        # --- update video frame ---
        vid.update()
        temp_surface.fill((0, 0, 0))
        vid.draw(temp_surface, (0, 0))
        screen.blit(temp_surface, (x_offset, y_offset))

        pygame.display.update()

        # Sync to video FPS
        if vid.fps:
            clock.tick(vid.fps)
        else:
            clock.tick(60)

        # Stop if video ends
        if not vid.active:
            running = False

    vid.close()
    pygame.quit()


if __name__ == "__main__":
    main()
