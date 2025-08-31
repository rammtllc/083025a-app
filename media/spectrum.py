import pygame
import random
import sys
import math
import time

# Initialize Pygame
pygame.init()

# Screen setup
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Faint Sweeping Vertical Oscillating Bars")
clock = pygame.time.Clock()

# Bar parameters
NUM_BARS = 50
BAR_HEIGHT = 10
BAR_SPACING = 2
AMPLITUDE = 100
SWEEP_SPEED = 150

# Bar class
class OscillatingBar:
    def __init__(self, index):
        self.index = index
        self.phase = random.uniform(0, 2*math.pi)
        self.speed = random.uniform(0.5, 2.0)
        self.direction = random.choice([-1, 1])
        # Very faint white, can adjust alpha
        self.color = (200, 200, 200, 25)  
        self.width = random.randint(50, 200)
        self.base_x = WIDTH // 2
        self.y = 0

    def update(self, t, sweep_y):
        self.x = self.base_x + math.sin(t * self.speed + self.phase) * AMPLITUDE * self.direction
        self.visible = sweep_y >= self.y and sweep_y <= self.y + BAR_HEIGHT

    def draw(self, surface):
        if self.visible:
            # Draw onto a temporary surface with alpha
            bar_surf = pygame.Surface((self.width, BAR_HEIGHT), pygame.SRCALPHA)
            bar_surf.fill(self.color)
            surface.blit(bar_surf, (int(self.x - self.width // 2), int(self.y)))

# Create stacked bars filling vertical center
bars = []
start_y = HEIGHT // 2 - ((NUM_BARS * (BAR_HEIGHT + BAR_SPACING)) // 2)
for i in range(NUM_BARS):
    bar = OscillatingBar(i)
    bar.y = start_y + i * (BAR_HEIGHT + BAR_SPACING)
    bars.append(bar)

# Main loop
start_time = time.time()
running = True
sweep_y = 0
while running:
    dt = clock.tick(60) / 1000.0
    t = time.time() - start_time
    sweep_y += SWEEP_SPEED * dt
    if sweep_y > HEIGHT:
        sweep_y = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            start_y = HEIGHT // 2 - ((NUM_BARS * (BAR_HEIGHT + BAR_SPACING)) // 2)
            for i, bar in enumerate(bars):
                bar.base_x = WIDTH // 2
                bar.y = start_y + i * (BAR_HEIGHT + BAR_SPACING)

    screen.fill((0, 0, 0))  # black background

    # Optional: faint sweep line
    sweep_surf = pygame.Surface((WIDTH, 2), pygame.SRCALPHA)
    sweep_surf.fill((200, 200, 255, 20))  # very faint
    screen.blit(sweep_surf, (0, sweep_y))

    # Update and draw bars
    for bar in bars:
        bar.update(t, sweep_y)
        bar.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
