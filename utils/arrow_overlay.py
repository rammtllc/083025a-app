# utils/arrow_overlay.py
import pygame

class ArrowOverlay:
    """
    Draws an arrow image on the screen at a given position, rotation, and scale,
    visible only between start_time and end_time.
    """

    def __init__(self, screen, params):
        """
        Parameters (in params dict):
            x, y : top-left coordinates
            rotation : angle in degrees
            start_time, end_time : seconds for visibility
            scale : scale factor for the image
            arrow_image_path : path to arrow image
        """
        self.screen = screen
        self.x = params.get("x", 0)
        self.y = params.get("y", 0)
        self.rotation = params.get("rotation", 0)
        self.start_time = params.get("start_time", 0)
        self.end_time = params.get("end_time", float('inf'))
        self.scale = params.get("scale", 1.0)
        self.image_path = params.get("arrow_image_path")

        # Load the arrow image
        self.original_image = pygame.image.load(self.image_path).convert_alpha()

        # Scale image according to the scale parameter
        orig_rect = self.original_image.get_rect()
        scaled_size = (int(orig_rect.width * self.scale), int(orig_rect.height * self.scale))
        self.image = pygame.transform.smoothscale(self.original_image, scaled_size)

        # Rotate image (pre-rotation)
        self.rotated_image = pygame.transform.rotate(self.image, self.rotation)
        self.rect = self.rotated_image.get_rect(topleft=(self.x, self.y))

    def update(self, current_time):
        """
        Blit the arrow onto the screen if the current_time is within start and end.
        """
        if self.start_time <= current_time <= self.end_time:
            self.screen.blit(self.rotated_image, (self.x, self.y))
