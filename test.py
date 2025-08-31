import pygame
from pyvidplayer2 import Video
#from moviepy.editor import VideoFileClip
from moviepy.video.io.VideoFileClip import VideoFileClip

pygame.init()

# Use MoviePy to get the video dimensions
clip = VideoFileClip("2025-08-3010-39-46.mp4")
vid_width, vid_height = clip.size  # width, height

# Set the window size to match video and make it resizable
win = pygame.display.set_mode((vid_width, vid_height), pygame.RESIZABLE)
pygame.display.set_caption("Video Player")

# Load video in pyvidplayer2
vid = Video("2025-08-3010-39-46.mp4")

clock = pygame.time.Clock()
running = True
temp_surface = pygame.Surface((vid_width, vid_height))

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            win_width, win_height = event.w, event.h
            win = pygame.display.set_mode((win_width, win_height), pygame.RESIZABLE)

    vid.update()
    temp_surface.fill((0, 0, 0))
    vid.draw(temp_surface, (0, 0))

    # Scale the video frame to fit the current window size
    scaled_surface = pygame.transform.smoothscale(temp_surface, win.get_size())
    win.blit(scaled_surface, (0, 0))
    pygame.display.update()

    if not vid.active:
        running = False

    clock.tick(60)

vid.close()
pygame.quit()
