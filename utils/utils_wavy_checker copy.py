# utils_wavy_checker.py
import pygame
import sys
import math
import time

pygame.init()

# ----------------------------
# Screen setup (configurable)
# ----------------------------
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wavy Checker Pattern")

clock = pygame.time.Clock()

# ----------------------------
# Draw functions
# ----------------------------
def draw_pulsing_background(surface, t):
    """Draw pulsing bluish-black background based on time t."""
    pulse = (math.sin(t) + 1) / 2  # 0..1
    blue_val = int(30 + 40 * pulse)  # 30–70
    bg_color = (blue_val // 2, blue_val // 2, blue_val)  # bluish-black
    surface.fill(bg_color)

def draw_wavy_checker(surface, t, spacing=40, wave_amplitude=20, wave_speed=1.0):
    """Draw moving wavy checkerboard lines."""
    line_color = (255, 255, 255)

    # Vertical wavy lines
    for x in range(0, WIDTH, spacing):
        points = []
        for y in range(0, HEIGHT, 20):
            offset = math.sin((y / 50.0) + t * wave_speed + x * 0.1) * wave_amplitude
            points.append((x + offset, y))
        pygame.draw.lines(surface, line_color, False, points, 1)

    # Horizontal wavy lines
    for y in range(0, HEIGHT, spacing):
        points = []
        for x in range(0, WIDTH, 20):
            offset = math.sin((x / 50.0) + t * wave_speed + y * 0.1) * wave_amplitude
            points.append((x, y + offset))
        pygame.draw.lines(surface, line_color, False, points, 1)

# ----------------------------
# Main loop runner
# ----------------------------
def run_wavy_checker():
    """Run the wavy checker pattern animation."""
    start_time = time.time()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        t = time.time() - start_time

        # Draw background + checker pattern
        draw_pulsing_background(screen, t)
        draw_wavy_checker(screen, t)

        pygame.display.flip()
        clock.tick(60)

# ----------------------------
# Entry point
# ----------------------------
#if __name__ == "__main__":
#    run_wavy_checker()
