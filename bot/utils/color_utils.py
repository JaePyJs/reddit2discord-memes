from PIL import Image

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
