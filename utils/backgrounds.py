import pygame
import math


import pygame
import math
import numpy as np

BLUE = (0, 150, 255)
BLACK = (0, 0, 0)
GRID_SPACING = 40  # default grid spacing

def create_radial_mask(radius, size):
    """Creates a radial gradient alpha mask using NumPy."""
    center_x, center_y = size[0] // 2, size[1] // 2
    y, x = np.ogrid[:size[1], :size[0]]
    dist = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)

    alpha = np.clip(255 - (dist / radius) * 255, 0, 255).astype(np.uint8)

    mask_array = np.zeros((size[1], size[0], 4), dtype=np.uint8)
    mask_array[..., 0:3] = 255  # white RGB
    mask_array[..., 3] = alpha  # radial alpha

    return pygame.image.frombuffer(mask_array.tobytes(), size, "RGBA")

def draw_net(surface, t, pulse, grid_spacing=GRID_SPACING):
    """Draw the pulsing net into a surface (transparent background)."""
    surface.fill((0, 0, 0, 0))
    width, height = surface.get_size()

    # Vertical lines
    sin_offsets_y = [
        math.sin(y * 0.01 + t) * 100 * pulse
        for y in range(0, height + grid_spacing, grid_spacing)
    ]
    for xi, x in enumerate(range(-width, width * 2, grid_spacing)):
        points = [(x + sin_offsets_y[yi], y)
                  for yi, y in enumerate(range(0, height + grid_spacing, grid_spacing))]
        if len(points) > 1:
            pygame.draw.lines(surface, BLUE, False, points, 1)

    # Horizontal lines
    for yi, y in enumerate(range(0, height + grid_spacing, grid_spacing)):
        points = [(x + math.sin(y * 0.01 + t) * 100 * pulse, y)
                  for x in range(-width, width * 2, grid_spacing)]
        if len(points) > 1:
            pygame.draw.lines(surface, BLUE, False, points, 1)

# ----------------------------
# Frame-based renderer
# ----------------------------
def play_circular_pulsing_net(screen, t=0, net_surface=None, mask_surface=None):
    """
    Draw one frame of the circular pulsing net.
    - t: current time in seconds
    - net_surface: cached surface to draw on (reuse for speed)
    - mask_surface: cached radial mask (reuse for speed)
    """
    if net_surface is None:
        net_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

    if mask_surface is None:
        size = screen.get_size()
        radius = min(size) // 2 - 20
        mask_surface = create_radial_mask(radius, size)

    # Animate pulse
    pulse = 1 + 0.2 * math.sin(t * 2)

    # Draw net and apply mask
    draw_net(net_surface, t, pulse)
    masked_surface = net_surface.copy()
    masked_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    # Render to screen
    screen.fill(BLACK)
    screen.blit(masked_surface, (0, 0))


# -------------------------
# Circular Pulsing Net
# -------------------------
def play_circular_pulsing_net2(screen, t=0):
    """Draw one frame of a circular pulsing net at time t (seconds)."""
    WIDTH, HEIGHT = screen.get_size()
    num_circles = 10
    for i in range(num_circles):
        radius = int(50 + 30 * math.sin(t * 2 + i))
        pygame.draw.circle(screen, (255, 255, 255), (WIDTH // 2, HEIGHT // 2), radius, 2)

# -------------------------
# Psychedelic Background
# -------------------------
def draw_psychedelic_background(screen, t=0):
    """Draw one frame of a rotating triangle psychedelic background at time t (seconds)."""
    WIDTH, HEIGHT = screen.get_size()
    triangle_count = 40
    for i in range(triangle_count):
        angle = t * 2 + i * 0.5
        x = WIDTH // 2 + int(math.cos(angle) * WIDTH // 2)
        y = HEIGHT // 2 + int(math.sin(angle) * HEIGHT // 2)
        color = (
            int(128 + 127 * math.sin(i + t * 3)),
            0,
            int(128 + 127 * math.cos(i + t * 2))
        )
        size = 100 + int(50 * math.sin(t + i))
        points = [
            (x, y - size // 2),
            (x - size // 2, y + size // 2),
            (x + size // 2, y + size // 2)
        ]
        pygame.draw.polygon(screen, color, points, width=2)


