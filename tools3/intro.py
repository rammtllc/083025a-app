# animated_intro_pygame.py
# Plays WAV audio and animates a transition between two images in fullscreen

import pygame
import sys
import time

# === PARAMETERS ===
audio_file = "intro_music.wav"
img1_file = "opening_screen.png"
img2_file = "banner.png"
screen_width, screen_height = 1280, 720
fps = 60
transition_duration = 5.0  # seconds for fade + swipe

# === INIT PYGAME ===
pygame.init()
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("YouTube Intro Animation")
clock = pygame.time.Clock()

# Load images and convert for faster blitting
img1 = pygame.image.load(img1_file).convert_alpha()
img2 = pygame.image.load(img2_file).convert_alpha()

# Scale images to screen
img1 = pygame.transform.scale(img1, (screen_width, screen_height))
img2 = pygame.transform.scale(img2, (screen_width, screen_height))

# === PLAY AUDIO ===
pygame.mixer.init()
pygame.mixer.music.load(audio_file)
pygame.mixer.music.play()

# === TRANSITION ANIMATION ===
num_frames = int(transition_duration * fps)

for i in range(num_frames):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Calculate fade factor
    fade = i / num_frames
    offset_x = int(-fade * screen_width)

    # Prepare surfaces
    img1_copy = img1.copy()
    img2_copy = img2.copy()

    img1_copy.set_alpha(int((1-fade)*255))
    img2_copy.set_alpha(int(fade*255))

    # Blit images
    screen.fill((0, 0, 0))
    screen.blit(img1_copy, (offset_x, 0))
    screen.blit(img2_copy, (screen_width + offset_x, 0))

    pygame.display.flip()
    clock.tick(fps)

# Keep the second image on screen for a few seconds
hold_time = 3  # seconds
start_time = time.time()
while time.time() - start_time < hold_time:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    screen.blit(img2, (0, 0))
    pygame.display.flip()
    clock.tick(fps)

pygame.mixer.music.stop()
pygame.quit()
print("✅ Animation complete")
