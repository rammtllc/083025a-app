import pygame
import random
import sys
import numpy  # <- Add this

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Glitch Effect Demo")
clock = pygame.time.Clock()

# Load image
image = pygame.image.load("background.jpg").convert()
image = pygame.transform.smoothscale(image, (WIDTH, HEIGHT))

def glitch_surface(surface, intensity=0.1):
    """Apply a glitch effect to a surface.
    intensity: 0-1, fraction of lines to distort.
    """
    w, h = surface.get_size()
    glitch_surf = surface.copy()

    # Random horizontal shifts
    for y in range(h):
        if random.random() < intensity:
            shift = random.randint(-20, 20)
            line = surface.subsurface((0, y, w, 1))
            glitch_surf.blit(line, (shift, y))
    
    # Optional RGB channel shift
    r, g, b = pygame.surfarray.array3d(glitch_surf).swapaxes(0, 1).T[:3]
    if random.random() < 0.3:
        r = numpy.roll(r, random.randint(-5, 5), axis=1)
        g = numpy.roll(g, random.randint(-5, 5), axis=1)
        b = numpy.roll(b, random.randint(-5, 5), axis=1)
        arr = numpy.stack([r, g, b], axis=2)
        pygame.surfarray.blit_array(glitch_surf, arr)
    
    return glitch_surf

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    glitched = glitch_surface(image, intensity=0.1)
    screen.blit(glitched, (0, 0))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
