import pygame
import os

def render_full_image(screen, params, current_time):
    """
    Renders a full-screen image (or scaled) based on event parameters.
    
    params: dict containing
        - image_path: path to the image
        - start_time: when to start rendering
        - end_time: when to stop rendering
        - x, y: position (None = center)
        - scale: float scale factor
    current_time: current elapsed time in seconds
    """
    start_time = float(params.get("start_time", 0))
    end_time = float(params.get("end_time", 9999))

    if not (start_time <= current_time <= end_time):
        return  # Not within the render window

    image_path = params.get("image_path")
    if not image_path or not os.path.exists(image_path):
        print(f"[WARN] Image file not found: {image_path}")
        return

    # Load image
    try:
        image = pygame.image.load(image_path).convert_alpha()
    except Exception as e:
        print(f"[ERROR] Failed to load image '{image_path}': {e}")
        return

    # Scale image if requested
    scale = float(params.get("scale", 1.0))
    if scale != 1.0:
        w, h = image.get_size()
        image = pygame.transform.smoothscale(image, (int(w*scale), int(h*scale)))

    # Position image
    x = params.get("x")
    y = params.get("y")
    if x is None:
        x = (screen.get_width() - image.get_width()) // 2
    if y is None:
        y = (screen.get_height() - image.get_height()) // 2

    # Draw
    screen.blit(image, (x, y))
