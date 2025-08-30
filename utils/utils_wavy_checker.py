import pygame
import math

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
# Visual effect runner (for use inside run_visuals)
# ----------------------------
def run_wavy_checker(surface, t, start=0, duration=9999):
    """
    Draw wavy checker on a given surface, only if t is within start..start+duration.
    
    surface  : pygame.Surface to draw on
    t        : current time in seconds
    start    : start time in seconds
    duration : duration in seconds
    """
    if not (start <= t <= start + duration):
        return

    width, height = surface.get_size()
    draw_pulsing_background(surface, t)
    draw_wavy_checker(surface, t, width, height)
