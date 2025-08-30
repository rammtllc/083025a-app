# utils_wavy_checker.py
import pygame
import math
import time

# ----------------------------
# Draw functions
# ----------------------------
def draw_pulsing_background(surface, t):
    """Draw pulsing bluish-black background based on time t."""
    pulse = (math.sin(t) + 1) / 2  # 0..1
    blue_val = int(30 + 40 * pulse)  # 30–70
    bg_color = (blue_val // 2, blue_val // 2, blue_val)  # bluish-black
    surface.fill(bg_color)


def draw_wavy_checker(surface, t, width, height, spacing=40, wave_amplitude=20, wave_speed=1.0):
    """Draw moving wavy checkerboard lines."""
    line_color = (255, 255, 255)

    # Vertical wavy lines
    for x in range(0, width, spacing):
        points = []
        for y in range(0, height, 20):
            offset = math.sin((y / 50.0) + t * wave_speed + x * 0.1) * wave_amplitude
            points.append((x + offset, y))
        pygame.draw.lines(surface, line_color, False, points, 1)

    # Horizontal wavy lines
    for y in range(0, height, spacing):
        points = []
        for x in range(0, width, 20):
            offset = math.sin((x / 50.0) + t * wave_speed + y * 0.1) * wave_amplitude
            points.append((x, y + offset))
        pygame.draw.lines(surface, line_color, False, points, 1)


# ----------------------------
# Visual effect runner with start/duration
# ----------------------------
def run_wavy_checker(start_time, duration, width=800, height=600):
    """
    Run the wavy checker animation only between start_time and start_time+duration.
    If duration=0, it runs indefinitely after start_time.
    """
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Wavy Checker Pattern")

    clock = pygame.time.Clock()
    global_start = time.time()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        now = time.time() - global_start

        # Only render during active window
        if now >= start_time and (duration == 0 or now <= start_time + duration):
            t = now - start_time
            draw_pulsing_background(screen, t)
            draw_wavy_checker(screen, t, width, height)
        else:
            screen.fill((0, 0, 0))  # Black when inactive

        pygame.display.flip()
        clock.tick(60)


# ----------------------------
# Entry point (demo)
# ----------------------------
#if __name__ == "__main__":
#    # Example: starts at 2s, lasts 10s
#    run_wavy_checker(start_time=2.0, duration=10.0)

# ----------------------------
# Entry point
# ----------------------------
#if __name__ == "__main__":
#    run_wavy_checker()
