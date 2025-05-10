from PIL import ImageDraw, ImageFont
import textwrap

def draw_wrapped_text(draw, text, font, box, fill, align='center', spacing=4):
    """
    Draws text wrapped to fit within the given bounding box.
    box: (x, y, width, height)
    Returns the y position after the last line.
    """
    x, y, w, h = box
    lines = []
    # Try wrapping text to fit the width
    for line in text.split('\n'):
        lines.extend(textwrap.wrap(line, width=20))  # width=20 is a default, will be resized
    # Find max width in pixels for font
    max_width = max([draw.textlength(line, font=font) for line in lines] + [1])
    # Adjust wrap width if text is too wide
    if max_width > w:
        # Estimate chars per line
        avg_char_width = max_width / max(len(line) for line in lines if line)
        wrap_width = max(1, int(w / avg_char_width))
        lines = []
        for line in text.split('\n'):
            lines.extend(textwrap.wrap(line, width=wrap_width))
    # Draw each line
    y_offset = y
    for line in lines:
        line_width = draw.textlength(line, font=font)
        if align == 'center':
            tx = x + (w - line_width) // 2
        elif align == 'right':
            tx = x + w - line_width
        else:
            tx = x
        draw.text((tx, y_offset), line, font=font, fill=fill)
        y_offset += font.getsize(line)[1] + spacing
    return y_offset
