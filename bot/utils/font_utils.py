from PIL import ImageFont

def get_best_fit_font(text, font_path, max_width, max_height, start_size=48, min_size=10):
    """
    Returns a font object with the largest size such that text fits in the given box.
    """
    size = start_size
    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        lines = text.split('\n')
        width = max([font.getsize(line)[0] for line in lines])
        height = sum([font.getsize(line)[1] for line in lines])
        if width <= max_width and height <= max_height:
            return font
        size -= 2
    return ImageFont.truetype(font_path, min_size)
