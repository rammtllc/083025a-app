import pygame
import librosa
import numpy as np
import glob
import time

class LipsyncPlayer:
    def __init__(self, audio_file="vocals.wav", image_pattern="mouth_*.png",
                 fps=30, img_size=(200, 200), min_frame=1, smooth_window=3):
        """
        audio_file: path to wav file
        image_pattern: glob pattern for mouth images
        fps: frames per second for mouth updates
        img_size: size to scale mouth images
        min_frame: minimum frame index for nonzero energy (avoid always closed mouth)
        smooth_window: size of smoothing window for energy (set 1 to disable)
        """
        self.audio_file = audio_file
        self.image_pattern = image_pattern
        self.fps = fps
        self.img_size = img_size
        self.min_frame = min_frame
        self.smooth_window = smooth_window

        # --- Load mouth images ---
        self.mouth_shapes = sorted(glob.glob(image_pattern))
        if not self.mouth_shapes:
            raise FileNotFoundError(f"No mouth images found matching {image_pattern}")

        self.num_shapes = len(self.mouth_shapes)
        self.mouth_imgs = []

        for f in self.mouth_shapes:
            img = pygame.image.load(f).convert_alpha()  # preserve alpha
            # Convert black background to transparent
            w, h = img.get_size()
            transparent_img = pygame.Surface((w, h), pygame.SRCALPHA)
            for x in range(w):
                for y in range(h):
                    color = img.get_at((x, y))
                    if color[:3] == (0, 0, 0):
                        transparent_img.set_at((x, y), (0, 0, 0, 0))
                    else:
                        transparent_img.set_at((x, y), color)
            # Scale to desired size
            transparent_img = pygame.transform.smoothscale(transparent_img, self.img_size)
            self.mouth_imgs.append(transparent_img)

        # --- Extract energy from audio ---
        y, sr = librosa.load(audio_file, sr=None)
        frame_length = int(0.025 * sr)  # 25 ms
        hop_length = int(sr / fps)

        energy = np.array([
            np.sum(np.abs(y[i:i + frame_length]) ** 2)
            for i in range(0, len(y), hop_length)
        ])

        # Normalize and threshold
        if energy.max() > energy.min():
            self.energy = np.interp(
                energy,
                (energy.min(), energy.max()),
                (self.min_frame, self.num_shapes - 1)
            ).astype(int)
        else:
            self.energy = np.zeros_like(energy, dtype=int)

        # Smooth energy for natural movement
        if smooth_window > 1:
            kernel = np.ones(smooth_window) / smooth_window
            self.energy = np.convolve(self.energy, kernel, mode='same').astype(int)

        self.running = False
        self.start_time = None

    def start(self):
        """Start audio playback and reset timer."""
        pygame.mixer.init()
        pygame.mixer.music.load(self.audio_file)
        pygame.mixer.music.play()
        self.start_time = time.time()
        self.running = True

    def update(self):
        """
        Return the current mouth surface based on audio energy.
        Returns None if audio finished.
        """
        if not self.running or not pygame.mixer.music.get_busy():
            self.running = False
            return None

        # Determine current frame based on elapsed time
        elapsed = time.time() - self.start_time
        frame_idx = int(elapsed * self.fps)
        if frame_idx >= len(self.energy):
            self.running = False
            return None

        idx = int(self.energy[frame_idx])
        idx = max(0, min(idx, self.num_shapes - 1))
        return self.mouth_imgs[idx]
