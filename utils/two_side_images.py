import pygame
from pygame import Surface
class TwoSideImagesAnimator:
    def __init__(self, screen: Surface, segment: dict, screen_width: int, screen_height: int):
        self.screen = screen
        self.segment = segment
        self.WIDTH = screen_width
        self.HEIGHT = screen_height

        # Load images
        self.img_left = pygame.image.load(segment["image_left"]).convert_alpha()
        self.img_right = pygame.image.load(segment["image_right"]).convert_alpha()

        # Scale factors with defaults
        scale_left = segment.get("image_left_scale", 1.0)
        scale_right = segment.get("image_right_scale", 1.0)

        # Scale images
        native_left = self.img_left.get_size()
        native_right = self.img_right.get_size()

        new_size_left = (int(native_left[0] * scale_left), int(native_left[1] * scale_left))
        new_size_right = (int(native_right[0] * scale_right), int(native_right[1] * scale_right))

        self.img_left = pygame.transform.smoothscale(self.img_left, new_size_left)
        self.img_right = pygame.transform.smoothscale(self.img_right, new_size_right)

        # Segment time info
        self.start = segment["start"]
        self.end = segment["end"]
        self.duration = self.end - self.start

        # Slide and zoom config
        self.slide_in = segment.get("image_slide_in", False)
        self.slide_delay = segment.get("image_slide_in_delay", 1.0)
        self.slide_duration = segment.get("image_slide_in_duration", 1.0)

        # Zoom config (hardcoded here, could be parameters if needed)
        self.ZOOM_IN_DURATION = 0.4
        self.ZOOM_HOLD_DURATION = 1.0
        self.ZOOM_OUT_DURATION = 0.4
        self.MAX_ZOOM = 2.5

        self.done = False  # <-- Added done flag

    def update(self, elapsed_time: float):
        """
        Call each frame with elapsed_time (seconds) since start of segment.
        This will draw the two images with slide-in and zoom animations accordingly.
        """

        if self.done:
            # After animation done, draw static images centered
            left_rect = self.img_left.get_rect(midright=(self.WIDTH // 2 - 10, self.HEIGHT // 2))
            right_rect = self.img_right.get_rect(midleft=(self.WIDTH // 2 + 10, self.HEIGHT // 2))
            self.screen.blit(self.img_left, left_rect)
            self.screen.blit(self.img_right, right_rect)
            return

        relative_t = elapsed_time - self.start

        if relative_t < 0:
            # Not started yet, skip drawing
            return

        if relative_t > self.duration:
            # Animation finished
            self.done = True
            # Draw static images one last time
            left_rect = self.img_left.get_rect(midright=(self.WIDTH // 2 - 10, self.HEIGHT // 2))
            right_rect = self.img_right.get_rect(midleft=(self.WIDTH // 2 + 10, self.HEIGHT // 2))
            self.screen.blit(self.img_left, left_rect)
            self.screen.blit(self.img_right, right_rect)
            return

        # --- Slide-in positions ---
        if self.slide_in:
            # LEFT IMAGE SLIDE-IN
            progress_left = min(max(relative_t / self.slide_duration, 0.0), 1.0)
            left_x = int(-self.img_left.get_width() + progress_left * ((self.WIDTH // 2 - 10) - (-self.img_left.get_width())))
            left_rect = self.img_left.get_rect(midright=(left_x, self.HEIGHT // 2))

            # RIGHT IMAGE SLIDE-IN
            if relative_t >= self.slide_delay:
                progress_right = min(max((relative_t - self.slide_delay) / self.slide_duration, 0.0), 1.0)
                right_x = int(self.WIDTH + (-self.WIDTH // 2 + 10) * progress_right)
            else:
                right_x = self.WIDTH
            right_rect = self.img_right.get_rect(midleft=(right_x, self.HEIGHT // 2))

            # Blit images on screen
            self.screen.blit(self.img_left, left_rect)
            self.screen.blit(self.img_right, right_rect)

            # --- Zoom animation after slide-in ---
            if relative_t >= self.slide_delay + self.slide_duration:
                zoom_time = relative_t - (self.slide_delay + self.slide_duration)
                total_zoom_phase = self.ZOOM_IN_DURATION + self.ZOOM_HOLD_DURATION + self.ZOOM_OUT_DURATION

                if zoom_time < total_zoom_phase:
                    # Zoom left image
                    if zoom_time < self.ZOOM_IN_DURATION:
                        factor = 1.0 + (self.MAX_ZOOM - 1.0) * (zoom_time / self.ZOOM_IN_DURATION)
                    elif zoom_time < self.ZOOM_IN_DURATION + self.ZOOM_HOLD_DURATION:
                        factor = self.MAX_ZOOM
                    else:
                        factor = self.MAX_ZOOM - (self.MAX_ZOOM - 1.0) * (
                            (zoom_time - self.ZOOM_IN_DURATION - self.ZOOM_HOLD_DURATION) / self.ZOOM_OUT_DURATION
                        )

                    zoomed_left = pygame.transform.smoothscale(
                        self.img_left,
                        (int(self.img_left.get_width() * factor), int(self.img_left.get_height() * factor))
                    )
                    zoomed_rect = zoomed_left.get_rect(bottomleft=left_rect.bottomleft)

                    # Draw background right, then zoomed left
                    self.screen.blit(self.img_right, right_rect)
                    self.screen.blit(zoomed_left, zoomed_rect)

                elif zoom_time < 2 * total_zoom_phase:
                    # Zoom right image
                    zoom_time_right = zoom_time - total_zoom_phase

                    if zoom_time_right < self.ZOOM_IN_DURATION:
                        factor = 1.0 + (self.MAX_ZOOM - 1.0) * (zoom_time_right / self.ZOOM_IN_DURATION)
                    elif zoom_time_right < self.ZOOM_IN_DURATION + self.ZOOM_HOLD_DURATION:
                        factor = self.MAX_ZOOM
                    else:
                        factor = self.MAX_ZOOM - (self.MAX_ZOOM - 1.0) * (
                            (zoom_time_right - self.ZOOM_IN_DURATION - self.ZOOM_HOLD_DURATION) / self.ZOOM_OUT_DURATION
                        )

                    zoomed_right = pygame.transform.smoothscale(
                        self.img_right,
                        (int(self.img_right.get_width() * factor), int(self.img_right.get_height() * factor))
                    )
                    zoomed_rect = zoomed_right.get_rect(bottomright=right_rect.bottomright)

                    # Draw background left, then zoomed right
                    self.screen.blit(self.img_left, left_rect)
                    self.screen.blit(zoomed_right, zoomed_rect)

                else:
                    # After both zooms done, show static images
                    self.screen.blit(self.img_left, left_rect)
                    self.screen.blit(self.img_right, right_rect)

        else:
            # No slide_in - just blit images centered at screen halves
            left_rect = self.img_left.get_rect(midright=(self.WIDTH // 2 - 10, self.HEIGHT // 2))
            right_rect = self.img_right.get_rect(midleft=(self.WIDTH // 2 + 10, self.HEIGHT // 2))
            self.screen.blit(self.img_left, left_rect)
            self.screen.blit(self.img_right, right_rect)
