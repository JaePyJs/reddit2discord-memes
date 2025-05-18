from PIL import Image
from typing import Tuple

def get_average_luminance(img, box):
    """
    Calculate the average luminance of the area in box (x, y, w, h).
    """
    x, y, w, h = box
    crop = img.crop((x, y, x+w, y+h)).convert('L')
    pixels = list(crop.getdata())
    return sum(pixels) / len(pixels) if pixels else 128


def pick_text_color(bg_luminance, light_color=(255,255,255), dark_color=(0,0,0), threshold=128):
    """
    Choose white or black text color based on background luminance.
    """
    return light_color if bg_luminance < threshold else dark_color


def get_contrasting_color(color: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """
    Get a contrasting color (black or white) based on the input color.

    Args:
        color: RGB color tuple

    Returns:
        Contrasting color (black or white)
    """
    # Calculate luminance using the formula: 0.299*R + 0.587*G + 0.114*B
    r, g, b = color
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

    # Return white for dark colors, black for light colors
    return (0, 0, 0) if luminance > 0.5 else (255, 255, 255)
