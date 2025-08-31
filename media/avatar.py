import pygame
import random
import sys
import math
import time
from utils.lipsync import LipsyncPlayer

# Init lipsync
#lipsync = LipsyncPlayer("vocals.wav", "mouth_*.png", fps=30, img_size=(120, 120))
#lipsync.start()

def adjust_brightness(surface, factor=1.0):
    """
    Adjust brightness of a surface while retaining transparency.
    factor < 1.0 -> darker
    factor = 1.0 -> unchanged
    factor > 1.0 -> brighter
    """
    # Extract RGB and Alpha
    arr_rgb = pygame.surfarray.pixels3d(surface).astype("float32")
    arr_alpha = pygame.surfarray.pixels_alpha(surface).copy()

    # Brightness adjust
    arr_rgb[:] = arr_rgb * factor
    arr_rgb[:] = arr_rgb.clip(0, 255)

    # Create new surface with alpha
    new_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.surfarray.blit_array(new_surface, arr_rgb.astype("uint8"))

    # Put alpha channel back
    pygame.surfarray.pixels_alpha(new_surface)[:] = arr_alpha

    return new_surface

# --- Utility functions ---
def desaturate(surface, amount=0.25):
    arr = pygame.surfarray.pixels3d(surface)
    gray = (0.3 * arr[:,:,0] + 0.59 * arr[:,:,1] + 0.11 * arr[:,:,2]).astype('uint8')
    arr[:,:,0] = arr[:,:,0] * (1 - amount) + gray * amount
    arr[:,:,1] = arr[:,:,1] * (1 - amount) + gray * amount
    arr[:,:,2] = arr[:,:,2] * (1 - amount) + gray * amount
    del arr
    return surface

def gaussian_blur(surface, passes=3, scale_factor=4):
    """
    Apply an approximate Gaussian blur using multiple downscale/upscale passes.
    passes: number of blur iterations (higher = smoother, slower)
    scale_factor: how much to shrink each pass (higher = blurrier)
    """
    if passes <= 0:
        return surface.copy()

    w, h = surface.get_size()
    blurred = surface.copy()

    for _ in range(passes):
        small = pygame.transform.smoothscale(
            blurred, 
            (max(1, w // scale_factor), max(1, h // scale_factor))
        )
        blurred = pygame.transform.smoothscale(small, (w, h))

    return blurred

def blur_surface(surface, amount=100):
    if amount <= 0:
        return surface
    scale = 1.0 / amount
    w, h = surface.get_size()
    small = pygame.transform.smoothscale(surface, (max(1,int(w*scale)), max(1,int(h*scale))))
    return pygame.transform.smoothscale(small, (w, h))

def scale_sprite(sprite, factor, bg_size):
    w = int(bg_size[0] * factor)
    h = int(sprite.get_height() * (w / sprite.get_width()))
    return pygame.transform.smoothscale(sprite, (w, h))

def get_sprite_position(rel_pos, bg_size, sprite_size):
    x = int(rel_pos[0] * bg_size[0])
    y = int(rel_pos[1] * bg_size[1])
    return (x, y)

def pendulum_offset(t, amplitude, speed, sharpen):
    angle = math.sin(t * speed)
    if sharpen != 1.0:
        angle = math.copysign(abs(angle)**sharpen, angle)
    return angle * amplitude

# --- Initialize Pygame ---
pygame.init()
WIN_WIDTH, WIN_HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Avatar App with Faint Sweeping Bars")
lipsync = LipsyncPlayer("vocals.wav", "mouth_*.png", fps=30, img_size=(120, 120))
lipsync.start()
clock = pygame.time.Clock()

# --- Load images ---
background_orig = pygame.image.load("background.jpg").convert()
avatar_orig = pygame.image.load("avatar.png").convert_alpha()
mouth_orig = pygame.image.load("mouth_00006.png").convert()
mouth_orig.set_colorkey((0,0,0))
mouth_orig = desaturate(mouth_orig, 0.5)
table_orig = pygame.image.load("table.png").convert_alpha()
computer_orig = pygame.image.load("computer.png").convert_alpha()
mic_orig = pygame.image.load("mic.png").convert_alpha()

# --- Sprite configuration ---
sprite_scales = {
    "avatar": 0.5,
    "mouth": 0.1,
    "table": 1.0,
    "computer": 0.27,
    "mic": 0.3
}
sprite_positions = {
    "avatar": (0.3, 0.0),
    "mouth": (0.5, 0.29),
    "table": (0.0, 0.2),
    "computer": (0.7, 0.5),
    "mic": (0.3, 0.6)
}

# --- Pendulum parameters ---
pendulum_amplitude = 10.0
pendulum_speed = 2.0
pendulum_sharpen = 1.0
pendulum_start_time = time.time()

# --- Ember effect ---
class Ember:
    def __init__(self):
        self.reset()
    def reset(self):
        self.y = random.uniform(0, WIN_HEIGHT)
        self.speed_y = random.uniform(-3, -0.5)
        self.x = random.uniform(0, WIN_WIDTH)
        self.radius = random.uniform(2,6)
        self.color = (random.randint(200,255), random.randint(50,120),0)
        self.speed_x = random.uniform(-1,1)
        self.alpha = random.randint(150,255)
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.alpha -= random.uniform(1,3)
        self.radius = max(0,self.radius-0.02)
        if self.alpha <=0 or self.y<0 or self.radius<=0:
            self.reset()
    def draw(self,surface):
        ember_surf = pygame.Surface((self.radius*2,self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(ember_surf, (*self.color,int(self.alpha)), (int(self.radius),int(self.radius)), int(self.radius))
        surface.blit(ember_surf,(self.x - self.radius, self.y - self.radius))

embers = [Ember() for _ in range(250)]

# --- Faint sweeping bars overlay ---
NUM_BARS = 50
BAR_HEIGHT = 10
BAR_SPACING = 2
AMPLITUDE_BAR = 100
SWEEP_SPEED = 150

class OscillatingBar:
    def __init__(self,index):
        self.index = index
        self.phase = random.uniform(0,2*math.pi)
        self.speed = random.uniform(0.5,2.0)
        self.direction = random.choice([-1,1])
        self.color = (255,255,255,15)  # very faint
        self.width = random.randint(50,200)
        self.base_x = WIN_WIDTH//2
        self.y = 0
        self.visible = False
    def update(self,t,sweep_y):
        self.x = self.base_x + math.sin(t*self.speed + self.phase) * AMPLITUDE_BAR * self.direction
        self.visible = sweep_y >= self.y and sweep_y <= self.y + BAR_HEIGHT
    def draw(self,surface):
        if self.visible:
            bar_surf = pygame.Surface((self.width,BAR_HEIGHT), pygame.SRCALPHA)
            bar_surf.fill(self.color)
            surface.blit(bar_surf, (int(self.x - self.width//2), int(self.y)))

bars = []
start_y = WIN_HEIGHT//2 - ((NUM_BARS*(BAR_HEIGHT+BAR_SPACING))//2)
for i in range(NUM_BARS):
    bar = OscillatingBar(i)
    bar.y = start_y + i*(BAR_HEIGHT+BAR_SPACING)
    bars.append(bar)

sweep_y = 0

# --- Main loop ---
running = True
while running:
    dt = clock.tick(60)/1000.0
    t = time.time() - pendulum_start_time
    sweep_y += SWEEP_SPEED*dt
    if sweep_y > WIN_HEIGHT:
        sweep_y = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            WIN_WIDTH, WIN_HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT), pygame.RESIZABLE)
            start_y = WIN_HEIGHT//2 - ((NUM_BARS*(BAR_HEIGHT+BAR_SPACING))//2)
            for i,bar in enumerate(bars):
                bar.base_x = WIN_WIDTH//2
                bar.y = start_y + i*(BAR_HEIGHT+BAR_SPACING)

    # --- Draw background & blur ---
    bg_width, bg_height = screen.get_size()
    background = pygame.transform.smoothscale(background_orig, (bg_width, bg_height))
    background = gaussian_blur(background, passes=6, scale_factor=4)
    screen.blit(background, (0, 0))

    # --- Draw embers ---
    for ember in embers:
        ember.update()
        ember.draw(screen)

    # --- Draw avatar & sprites ---
    avatar = scale_sprite(avatar_orig, sprite_scales["avatar"], (bg_width,bg_height))
    #mouth = scale_sprite(mouth_orig, sprite_scales["mouth"], (bg_width,bg_height))
    # --- Lipsync mouth ---
    #x_offset = pendulum_offset(t, pendulum_amplitude, pendulum_speed, pendulum_sharpen)
    #mouth_surface = lipsync.update()
    #if mouth_surface:
    # Scale mouth relative to background
        #mouth_surface.set_colorkey((0, 0, 0))
    #    mouth_surface = lipsync.update()
    #    if mouth_surface:
    #        mouth = scale_sprite(mouth_surface, sprite_scales["mouth"], (bg_width, bg_height))
    #        mouth_pos = (
    #            get_sprite_position(sprite_positions["mouth"], (bg_width,bg_height), mouth.get_size())[0] + x_offset,
    #            get_sprite_position(sprite_positions["mouth"], (bg_width,bg_height), mouth.get_size())[1]
    #        )
    #        screen.blit(mouth, mouth_pos)

    x_offset = pendulum_offset(t, pendulum_amplitude, pendulum_speed, pendulum_sharpen)
    mouth_surface = lipsync.update()
    if mouth_surface:
        mouth = scale_sprite(mouth_surface, sprite_scales["mouth"], (bg_width, bg_height))
        mouth_pos = (
            get_sprite_position(sprite_positions["mouth"], (bg_width,bg_height), mouth.get_size())[0] + x_offset,
            get_sprite_position(sprite_positions["mouth"], (bg_width,bg_height), mouth.get_size())[1]
        )
        screen.blit(mouth, mouth_pos)

        mouth = scale_sprite(mouth_surface, sprite_scales["mouth"], (bg_width, bg_height))
    # Compute position with avatar sway
        mouth_pos = (
            get_sprite_position(sprite_positions["mouth"], (bg_width,bg_height), mouth.get_size())[0] + x_offset,
            get_sprite_position(sprite_positions["mouth"], (bg_width,bg_height), mouth.get_size())[1]
        )
        screen.blit(mouth, mouth_pos)

    table = scale_sprite(table_orig, sprite_scales["table"], (bg_width,bg_height))
    #table = adjust_brightness(table, 0.6)   # make desk darker (60% brightness)
    table = scale_sprite(table_orig, sprite_scales["table"], (bg_width, bg_height))
    table = adjust_brightness(table, 0.6)   # 60% brightness but keeps transparent edges

    computer = scale_sprite(computer_orig, sprite_scales["computer"], (bg_width,bg_height))
    mic = scale_sprite(mic_orig, sprite_scales["mic"], (bg_width,bg_height))


    avatar_pos = (get_sprite_position(sprite_positions["avatar"], (bg_width,bg_height), avatar.get_size())[0]+x_offset,
                  get_sprite_position(sprite_positions["avatar"], (bg_width,bg_height), avatar.get_size())[1])
    mouth_pos = (get_sprite_position(sprite_positions["mouth"], (bg_width,bg_height), mouth.get_size())[0]+x_offset,
                 get_sprite_position(sprite_positions["mouth"], (bg_width,bg_height), mouth.get_size())[1])

    screen.blit(avatar, avatar_pos)
    screen.blit(mouth, mouth_pos)
    screen.blit(table, get_sprite_position(sprite_positions["table"], (bg_width,bg_height), table.get_size()))
    screen.blit(computer, get_sprite_position(sprite_positions["computer"], (bg_width,bg_height), computer.get_size()))
    screen.blit(mic, get_sprite_position(sprite_positions["mic"], (bg_width,bg_height), mic.get_size()))

    # --- Draw faint sweeping bars overlay ---
    for bar in bars:
        bar.update(t,sweep_y)
        bar.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
