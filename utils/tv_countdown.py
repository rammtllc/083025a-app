# utils/tv_countdown.py
import pygame
import time

class TVCountdownWithBurst:
    """
    Displays a TV-style countdown with a burst animation at the end.

    Example usage:
        screen = pygame.display.set_mode((800, 600))
        countdown = TVCountdownWithBurst(screen)
        while not countdown.done:
            countdown.update()
    """
    def __init__(self, screen, countdown_start=3, countdown_duration=1.0, burst_duration=1.0,
                 font_size=200, font_color=(255, 255, 255), bg_color=(0, 0, 0), start_time=0.0):
        self.screen = screen
        self.screen_width, self.screen_height = screen.get_size()
        self.countdown = countdown_start
        self.countdown_duration = countdown_duration
        self.burst_duration = burst_duration

        self.font_size = font_size
        self.font_color = font_color
        self.bg_color = bg_color
        self.font = pygame.font.SysFont(None, self.font_size, bold=True)

        self.start_time = start_time  # <-- start time from event JSON
        self.burst_start_time = None
        self.burst_max_radius = int(max(self.screen_width, self.screen_height) * 1.5)

        self.done = False
        self.clock = pygame.time.Clock()
        self.internal_elapsed = 0.0  # elapsed relative to countdown start

    def update(self, current_time):
        """Update countdown based on current_time from run_visuals."""
        if self.done:
            return

        elapsed = current_time - self.start_time
        if elapsed < 0:
            return  # not started yet

        self.internal_elapsed = elapsed

        self.screen.fill(self.bg_color)

        if self.countdown > 0:
            text_surface = self.font.render(str(self.countdown), True, self.font_color)
            rect = text_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(text_surface, rect)

            if self.internal_elapsed >= self.countdown_duration:
                self.countdown -= 1
                self.start_time += self.countdown_duration
                self.internal_elapsed = 0.0

        elif self.countdown == 0:
            if self.burst_start_time is None:
                self.burst_start_time = current_time

            burst_elapsed = current_time - self.burst_start_time
            progress = min(burst_elapsed / self.burst_duration, 1.0)

            radius = int(progress * self.burst_max_radius)
            alpha = int(255 * (1 - progress))

            burst_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            pygame.draw.circle(burst_surface, (*self.font_color, alpha),
                               (self.screen_width // 2, self.screen_height // 2), radius)
            self.screen.blit(burst_surface, (0, 0))

            if progress >= 1.0:
                self.done = True
