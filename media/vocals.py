import pygame
import librosa
import numpy as np
import time
import glob
import os

# === CONFIG ===
AUDIO_FILE = "vocals.wav"
FPS = 30  # frames per second

# === STEP 1: Find all mouth PNGs ===
MOUTH_SHAPES = sorted(glob.glob("mouth_*.png"))
if not MOUTH_SHAPES:
    raise FileNotFoundError("No mouth_*.png files found in the current folder!")

num_shapes = len(MOUTH_SHAPES)
print(f"Loaded {num_shapes} mouth images")

# === STEP 2: Load audio and extract features ===
y, sr = librosa.load(AUDIO_FILE, sr=None)

frame_length = int(0.025 * sr)  # 25 ms window
hop_length = int(sr / FPS)      # match display FPS
energy = np.array([
    np.sum(np.abs(y[i:i+frame_length])**2)
    for i in range(0, len(y), hop_length)
])

# Normalize energy to [0, num_shapes-1]
if energy.max() > energy.min():
    energy = np.interp(energy, (energy.min(), energy.max()), (0, num_shapes-1)).astype(int)
else:
    energy = np.zeros_like(energy, dtype=int)

# === STEP 3: Initialize pygame ===
pygame.init()
screen = pygame.display.set_mode((400, 400))
pygame.display.set_caption("Lip Sync")

mouth_imgs = [pygame.image.load(f).convert_alpha() for f in MOUTH_SHAPES]
mouth_imgs = [pygame.transform.smoothscale(img, (200, 200)) for img in mouth_imgs]

# === STEP 4: Play audio and animate ===
pygame.mixer.init()  # let pygame decide frequency
pygame.mixer.music.load(AUDIO_FILE)
pygame.mixer.music.play()

frame = 0
running = True

while running and pygame.mixer.music.get_busy():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if frame < len(energy):
        idx = int(energy[frame])
        idx = max(0, min(idx, num_shapes-1))  # clamp to valid range
        screen.fill((0, 0, 0))
        screen.blit(mouth_imgs[idx], (100, 100))
        pygame.display.flip()
        frame += 1

    time.sleep(1.0 / FPS)

pygame.quit()
