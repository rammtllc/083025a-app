import pygame
import math

# ----------------------------
# Spin & Fade Transition
# ----------------------------
def spin_fade(surface, screen, duration=2000):
    """
    Spins and fades out the given surface over a duration (in ms).
    """
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()

    width, height = surface.get_size()
    center = (screen.get_width() // 2, screen.get_height() // 2)

    while True:
        elapsed = pygame.time.get_ticks() - start_time
        if elapsed > duration:
            break

        progress = elapsed / duration
        angle = progress * 360
        alpha = 255 * (1 - progress)

        rotated = pygame.transform.rotate(surface, angle)
        rotated.set_alpha(int(alpha))
        rect = rotated.get_rect(center=center)

        screen.fill((0, 0, 0))
        screen.blit(rotated, rect.topleft)
        pygame.display.flip()
        clock.tick(60)


# ----------------------------
# Swirl Effect Transition
# ----------------------------
def swirl_effect(surface, screen, duration=2000, swirl_strength=5):
    """
    Applies a swirl effect transition on the given surface.
    """
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    center_x, center_y = screen.get_width() // 2, screen.get_height() // 2

    while True:
        elapsed = pygame.time.get_ticks() - start_time
        if elapsed > duration:
            break

        progress = elapsed / duration
        swirl_angle = swirl_strength * progress * math.pi * 2

        distorted = pygame.Surface(surface.get_size())
        distorted.fill((0, 0, 0))

        for y in range(surface.get_height()):
            for x in range(surface.get_width()):
                dx = x - center_x
                dy = y - center_y
                distance = math.hypot(dx, dy)
                angle = math.atan2(dy, dx) + swirl_angle * (distance / max(center_x, center_y))

                src_x = int(center_x + distance * math.cos(angle))
                src_y = int(center_y + distance * math.sin(angle))

                if 0 <= src_x < surface.get_width() and 0 <= src_y < surface.get_height():
                    distorted.set_at((x, y), surface.get_at((src_x, src_y)))

        screen.blit(distorted, (0, 0))
        pygame.display.flip()
        clock.tick(60)
