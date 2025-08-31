import pygame
import os
import time
import json
import shutil

# ----------------------------
# Update schedule from MP3
# ----------------------------
def update_event_schedule_from_mp3(settings_path, voiceover_path):
    """
    Updates event_schedule.json path in default_settings.json
    and overwrites its events with start/middle/end markers
    based on MP3 duration.
    """
    if not os.path.exists(settings_path):
        print(f"[WARN] Settings file not found: {settings_path}")
        return

    if not os.path.exists(voiceover_path):
        print(f"[WARN] Voiceover file not found: {voiceover_path}")
        return

    # Initialize pygame mixer and get duration
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        sound = pygame.mixer.Sound(voiceover_path)
        duration = sound.get_length()  # duration in seconds
    except Exception as e:
        print(f"[ERROR] Could not read MP3 duration: {e}")
        return

    # Divide duration into thirds
    third = duration / 3 if duration else 0.0
    event_schedule = [
        {"time": 0.0, "action": "start"},
        {"time": third, "action": "middle"},
        {"time": 2 * third, "action": "end"}
    ]

    # Load existing settings
    with open(settings_path, "r") as f:
        settings = json.load(f)

    # Ensure event_schedule.json path is set
    events_file = settings.get("event_schedule_path")
    if not events_file:
        media_dir = os.path.abspath(os.path.join(os.path.dirname(settings_path), "media"))
        events_file = os.path.join(media_dir, "event_schedule.json")
        settings["event_schedule_path"] = events_file

    os.makedirs(os.path.dirname(events_file), exist_ok=True)

    # Backup and overwrite event_schedule.json
    if os.path.exists(events_file):
        backup_file = events_file + ".bak"
        shutil.copy2(events_file, backup_file)
        print(f"[INFO] Backup created at {backup_file}")

    with open(events_file, "w") as f:
        json.dump({"events": event_schedule}, f, indent=2)

    # Save updated settings
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"[INFO] Event schedule overwritten from MP3 duration ({duration:.3f}s)")


# ----------------------------
# Helper to play voiceover MP3
# ----------------------------
def play_voiceover(voiceover_path):
    if not voiceover_path or not os.path.exists(voiceover_path):
        print(f"[WARN] Voiceover file not found: {voiceover_path}")
        return False
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(voiceover_path)
        pygame.mixer.music.play()
        return True
    except Exception as e:
        print(f"[ERROR] Could not play voiceover: {e}")
        return False


# ----------------------------
# Helper generator for words or sentences
# ----------------------------
def text_by_second(timestamps, start_time=None):
    if start_time is None:
        start_time = time.time()
    idx = 0
    text_to_show = ""
    while idx < len(timestamps):
        elapsed = time.time() - start_time
        while idx < len(timestamps) and float(timestamps[idx]["time"]) <= elapsed:
            text_to_show = timestamps[idx]["text"]
            idx += 1
        yield text_to_show
    while True:
        yield text_to_show


# ----------------------------
# Timestamp overlay helper (0.000 format)
# ----------------------------
def render_timestamps(screen, font, start_time, end_time):
    run_seconds = time.time() - start_time
    elapsed_text = font.render(f"Elapsed: {run_seconds:06.3f}s", True, (255, 255, 255))
    screen.blit(elapsed_text, (10, 10))
    end_text = font.render(f"End: {end_time:06.3f}s", True, (255, 255, 255))
    screen.blit(end_text, (screen.get_width() - end_text.get_width() - 10, 10))


# ----------------------------
# Main visuals
# ----------------------------
import os
import time
import json
import pygame
from utils.backgrounds import play_circular_pulsing_net, draw_psychedelic_background
from utils.transitions import spin_fade, swirl_effect
from utils.full_image import render_full_image
from utils.two_side_images import TwoSideImagesAnimator

# ----------------------------
# Event schedule updater
# ----------------------------
def update_event_schedule_from_mp3(settings_path, voiceover_path):
    if not os.path.exists(settings_path) or not os.path.exists(voiceover_path):
        print(f"[WARN] Missing settings or voiceover file.")
        return

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        duration = pygame.mixer.Sound(voiceover_path).get_length()
    except Exception as e:
        print(f"[ERROR] Could not read MP3 duration: {e}")
        return

    third = duration / 3 if duration else 0.0
    event_schedule = [
        {"time": 0.0, "action": "start"},
        {"time": third, "action": "middle"},
        {"time": 2 * third, "action": "end"}
    ]

    with open(settings_path, "r") as f:
        settings = json.load(f)

    events_file = settings.get("event_schedule_path") or os.path.join(
        os.path.dirname(settings_path), "media", "event_schedule.json"
    )
    settings["event_schedule_path"] = events_file
    os.makedirs(os.path.dirname(events_file), exist_ok=True)

    if os.path.exists(events_file):
        shutil.copy2(events_file, events_file + ".bak")

    with open(events_file, "w") as f:
        json.dump({"events": event_schedule}, f, indent=2)

    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

# ----------------------------
# Voiceover and text helpers
# ----------------------------
def play_voiceover(voiceover_path):
    if not os.path.exists(voiceover_path):
        return False
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(voiceover_path)
        pygame.mixer.music.play()
        return True
    except Exception as e:
        print(f"[ERROR] Could not play voiceover: {e}")
        return False

def text_by_second(timestamps, start_time=None):
    if start_time is None:
        start_time = time.time()
    idx = 0
    text_to_show = ""
    while idx < len(timestamps):
        elapsed = time.time() - start_time
        while idx < len(timestamps) and float(timestamps[idx]["time"]) <= elapsed:
            text_to_show = timestamps[idx]["text"]
            idx += 1
        yield text_to_show
    while True:
        yield text_to_show

def render_timestamps(screen, font, start_time, end_time):
    elapsed = time.time() - start_time
    elapsed_text = font.render(f"Elapsed: {elapsed:06.3f}s", True, (255, 255, 255))
    screen.blit(elapsed_text, (10, 10))
    end_text = font.render(f"End: {end_time:06.3f}s", True, (255, 255, 255))
    screen.blit(end_text, (screen.get_width() - end_text.get_width() - 10, 10))

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
# Main visuals
# ----------------------------
import os
import time
import json
import pygame
import cv2
import numpy as np
from utils.backgrounds import play_circular_pulsing_net, draw_psychedelic_background
from utils.utils_wavy_checker import run_wavy_checker
from utils.transitions import spin_fade, swirl_effect
from utils.full_image import render_full_image
from utils.two_side_images import TwoSideImagesAnimator
from utils.tv_countdown import TVCountdownWithBurst
from utils.arrow_overlay import ArrowOverlay
from utils.video_utils import VideoPlayer

def run_visuals(timestamps, event_schedule, font_name, font_size, settings, data=None, screen=None):
    # ----------------------------
    # Create main window 1600x600
    # ----------------------------
    if screen is None:
        screen = pygame.display.set_mode((1600, 600))
        pygame.display.set_caption("Visuals + Video")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    events_file = settings.get("event_schedule_path") or os.path.join(base_dir, "..", "media", "event_schedule.json")
    video_path = os.path.join(base_dir, "..", "media", "demo.mp4")
    settings["event_schedule_path"] = events_file

    # ----------------------------
    # Load event schedule
    # ----------------------------
    if os.path.exists(events_file):
        with open(events_file, "r") as f:
            file_data = json.load(f)
        event_schedule[:] = file_data.get("events", [])
    else:
        event_schedule[:] = []

    end_time = max(
        [float(e.get("time", 0)) for e in event_schedule if "time" in e] +
        [float(t.get("time", 0)) for t in timestamps],
        default=0.0
    )

    # ----------------------------
    # Play voiceover
    # ----------------------------
    voiceover_path = settings.get("voiceover_path")
    if voiceover_path and os.path.exists(voiceover_path):
        play_voiceover(voiceover_path)

    clock = pygame.time.Clock()

    # ----------------------------
    # Load video (right side)
    # ----------------------------
    cap = None
    video_surf = None
    video_area = pygame.Rect(800, 0, 800, 600)
    if os.path.exists(video_path):
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            video_surf = pygame.Surface((video_area.width, video_area.height))
            print(f"[INFO] Video opened: {video_path}")
        else:
            print(f"[ERROR] Could not open video: {video_path}")
            cap = None
    else:
        print(f"[ERROR] Video file not found: {video_path}")

    # ----------------------------
    # Font setup
    # ----------------------------
    try:
        font = pygame.font.Font(font_name, font_size)
    except:
        font = pygame.font.SysFont(None, font_size)

    start_time_global = time.time()
    text_gen = text_by_second(timestamps, start_time=start_time_global)
    two_side_animators = {}

    # Background events
    background_events = [e for e in event_schedule if e.get("event") in ("circular_pulsing_net", "psychedelic_background", "run_wavy_checker")]

    # Medium-priority events
    medium_priority_events = {}
    for event in event_schedule:
        ev_type = event.get("event")
        key = id(event)
        params = event.get("params", {})
        left_sub = screen.subsurface((0, 0, 800, 600))

        if ev_type == "tv_countdown":
            medium_priority_events[key] = TVCountdownWithBurst(left_sub, start_time=float(event.get("start_time", 0)))
        elif ev_type == "arrow_overlay":
            medium_priority_events[key] = ArrowOverlay(left_sub, params)
        elif ev_type == "centered_video":
            medium_priority_events[key] = VideoPlayer(left_sub,
                                                      video_path=params["video_path"],
                                                      start_time=params.get("start_time", 0),
                                                      end_time=params.get("end_time", float('inf')),
                                                      scale=params.get("scale", 0.5),
                                                      colorkey=params.get("colorkey", (0,0,0)))

    # ----------------------------
    # Main loop
    # ----------------------------
    running = True
    while running:
        current_time = time.time() - start_time_global

        # Clear left and right halves
        screen.fill((30,30,30), rect=pygame.Rect(0,0,800,600))    # left visuals
        screen.fill((0,0,0), rect=pygame.Rect(800,0,800,600))     # right video
        left_surface = screen.subsurface((0,0,800,600))

        # ----------------------------
        # LEFT: Backgrounds
        # ----------------------------
        for bg_event in background_events:
            start = float(bg_event.get("start_time", 0))
            duration = float(bg_event.get("params", {}).get("duration", 9999))
            if start <= current_time <= start + duration:
                if bg_event.get("event") == "circular_pulsing_net":
                    play_circular_pulsing_net(left_surface, t=current_time)
                elif bg_event.get("event") == "psychedelic_background":
                    draw_psychedelic_background(left_surface, t=current_time)
                elif bg_event.get("event") == "run_wavy_checker":
                    run_wavy_checker(left_surface, t=current_time, start=start, duration=duration)

        # ----------------------------
        # LEFT: Middle-priority events
        # ----------------------------
        for event in event_schedule:
            ev_type = event.get("event")
            params = event.get("params", {})
            event_start = float(event.get("start_time", event.get("time", 0)))
            event_end = event_start + float(params.get("duration", 5))
            if not (event_start <= current_time <= event_end):
                continue
            if ev_type == "spin_fade":
                spin_fade(left_surface.copy(), left_surface, int(params.get("duration", 2)*1000))
            elif ev_type == "swirl_effect":
                swirl_effect(left_surface.copy(), left_surface, int(params.get("duration", 2)*1000),
                             params.get("swirl_strength", 5))
            elif ev_type == "two_side_images":
                key = id(event)
                if key not in two_side_animators:
                    animator = TwoSideImagesAnimator(left_surface,
                                                     segment=params["segment"],
                                                     screen_width=800, screen_height=600)
                    two_side_animators[key] = animator
                two_side_animators[key].update(current_time)
            elif ev_type == "full_image":
                render_full_image(left_surface, params, current_time)

        # ----------------------------
        # LEFT: Medium-priority updates
        # ----------------------------
        for mp_event in medium_priority_events.values():
            mp_event.update(current_time)

        # ----------------------------
        # LEFT: Text overlay
        # ----------------------------
        text_to_show = next(text_gen)
        if text_to_show:
            text_surface = font.render(text_to_show, True, (255,255,255))
            left_surface.blit(text_surface, (50,50))
        render_timestamps(left_surface, font, start_time_global, end_time)

        # ----------------------------
        # RIGHT: Video
        # ----------------------------
        if cap and video_surf:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (video_area.width, video_area.height))
                pygame.surfarray.blit_array(video_surf, frame_resized.swapaxes(0,1))
                screen.blit(video_surf, (video_area.x, video_area.y))

        # ----------------------------
        # Display
        # ----------------------------
        pygame.display.flip()
        clock.tick(60)

        # Quit events
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
                pygame.mixer.music.stop()

        if current_time > end_time:
            running = False
            pygame.mixer.music.stop()

    # Release video capture
    if cap:
        cap.release()
