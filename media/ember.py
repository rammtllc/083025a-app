import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Screen settings (fullscreen)
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Lively Fireplace Ember Effect")
clock = pygame.time.Clock()

# Particle class
class Ember:
    def __init__(self):
        self.reset()

    def reset(self):
        # 15% chance to start higher and rise faster
        if random.random() < 0.15:
            self.y = random.uniform(50, HEIGHT - 50)  # high start
            self.speed_y = random.uniform(-1.5, -4.0)
        else:
            self.y = random.uniform(HEIGHT - 50, HEIGHT)  # bottom start
            self.speed_y = random.uniform(-0.5, -3.0)
        self.x = random.uniform(0, WIDTH)
        self.radius = random.uniform(2, 6)
        self.color = (random.randint(200, 255), random.randint(50, 120), 0)  # red-orange glow
        self.speed_x = random.uniform(-1.0, 1.0)
        self.alpha = random.randint(150, 255)  # varied brightness

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.alpha -= random.uniform(1, 3)
        self.radius = max(0, self.radius - 0.02)
        # Reset if gone off-screen, faded, or shrunk
        if self.alpha <= 0 or self.y < 0 or self.radius <= 0:
            self.reset()

    def draw(self, surface):
        ember_surf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(ember_surf, (*self.color, int(self.alpha)), (int(self.radius), int(self.radius)), int(self.radius))
        surface.blit(ember_surf, (self.x - self.radius, self.y - self.radius))

# Create many embers for full screen
embers = [Ember() for _ in range(250)]  # increase for more liveliness

# Main loop
running = True
while running:
    screen.fill((0, 0, 0))  # black background

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            # Reset all embers for new size
            for ember in embers:
                ember.reset()

    # Update and draw embers
    for ember in embers:
        ember.update()
        ember.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
