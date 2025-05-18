from PIL import ImageFont, Image, ImageDraw

def get_best_fit_font(text, font_path, max_width, max_height, start_size=48, min_size=10):
    """
    Returns a font object with the largest size such that text fits in the given box.
    Uses modern Pillow methods for font size calculation.
    """
    # Use a default font if the specified font is not available
    if not font_path:
        font_path = ImageFont.load_default()

    size = start_size
    while size >= min_size:
        try:
            font = ImageFont.truetype(font_path, size)
            lines = text.split('\n')

            # Create a temporary drawing context to measure text
            # This is more accurate than using getsize which is deprecated
            img = Image.new('RGB', (1, 1))
            draw = ImageDraw.Draw(img)

            # Calculate width and height using getbbox (modern method)
            widths = []
            heights = []
            for line in lines:
                if not line:  # Handle empty lines
                    heights.append(size)  # Approximate height for empty line
                    widths.append(0)
                    continue

                # Get bounding box for text
                bbox = draw.textbbox((0, 0), line, font=font)
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                widths.append(width)
                heights.append(height)

            # Check if text fits in the box
            max_line_width = max(widths) if widths else 0
            total_height = sum(heights)

            if max_line_width <= max_width and total_height <= max_height:
                return font
        except Exception as e:
            # If there's an error with this font size, try a smaller one
            print(f"Font error at size {size}: {e}")

        size -= 2

    # If no size fits, return the smallest allowed size
    try:
        return ImageFont.truetype(font_path, min_size)
    except Exception:
        # Fallback to default font if everything else fails
        return ImageFont.load_default()
