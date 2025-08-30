import cv2
import pygame
import time

# utils/video_utils.py
import cv2
import pygame

class VideoPlayer:
    def __init__(self, screen, video_path, start_time=0, end_time=None, scale=0.5, colorkey=(0,0,0)):
        self.screen = screen
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.scale = scale
        self.colorkey = colorkey
        self.start_time = start_time
        self.end_time = end_time if end_time is not None else float('inf')
        self.screen_width, self.screen_height = screen.get_size()
        self.target_width = int(self.screen_width * scale)
        self.target_height = int(self.screen_height * scale)

    def update(self, current_time):
        if not (self.start_time <= current_time <= self.end_time):
            return  # not time yet

        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # loop if needed
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (self.target_width, self.target_height))
        frame_surface = pygame.Surface((self.target_width, self.target_height), pygame.SRCALPHA)
        frame_surface.blit(pygame.surfarray.make_surface(frame.swapaxes(0,1)), (0,0))
        frame_surface.set_colorkey(self.colorkey)

        x = (self.screen_width - self.target_width) // 2
        y = (self.screen_height - self.target_height) // 2
        self.screen.blit(frame_surface, (x, y))


def play_centered_video(screen, video_path, scale=0.5, colorkey=(0, 0, 0)):
    """
    Play a video centered on the screen scaled to the given scale,
    with transparency on the given colorkey color.

    Args:
        screen (pygame.Surface): The pygame screen to draw on.
        video_path (str): Path to the video file.
        scale (float): Scale of the video relative to screen size (0 < scale <= 1).
        colorkey (tuple): RGB color to treat as transparent.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {video_path}")
        return

    screen_width, screen_height = screen.get_size()
    target_width = int(screen_width * scale)
    target_height = int(screen_height * scale)

    clock = pygame.time.Clock()
    running = True

    while running:
        ret, frame = cap.read()
        if not ret:
            break  # Video ended

        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Resize frame
        frame = cv2.resize(frame, (target_width, target_height))

        # Convert numpy array to pygame surface
        frame_surface = pygame.Surface((target_width, target_height), pygame.SRCALPHA)
        pygame.surfarray.blit_array(frame_surface, frame.swapaxes(0, 1))

        # Set colorkey for transparency
        frame_surface.set_colorkey(colorkey)

        # Calculate centered position
        x = (screen_width - target_width) // 2
        y = (screen_height - target_height) // 2

        # Blit the video frame
        screen.blit(frame_surface, (x, y))
        pygame.display.flip()

        # Handle events to keep window responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        clock.tick(30)  # Limit to 30 FPS

    cap.release()