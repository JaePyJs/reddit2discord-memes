from PIL import Image, ImageDraw, ImageFont
import os

def add_watermark(img_path, output_path, text='@YourMemeBot', font_path=None, font_size=24, opacity=128, pos='bottom_right', margin=10):
    """
    Adds a semi-transparent watermark text to the image.
    pos: 'bottom_right', 'bottom_left', 'top_right', 'top_left'
    margin: pixel margin from the edge
    """
    img = Image.open(img_path).convert('RGBA')
    txt_layer = Image.new('RGBA', img.size, (255,255,255,0))
    font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    draw = ImageDraw.Draw(txt_layer)
    text_width, text_height = draw.textsize(text, font=font)
    if pos == 'bottom_right':
        x = img.width - text_width - margin
        y = img.height - text_height - margin
    elif pos == 'bottom_left':
        x = margin
        y = img.height - text_height - margin
    elif pos == 'top_right':
        x = img.width - text_width - margin
        y = margin
    else:
        x = margin
        y = margin
    draw.text((x, y), text, font=font, fill=(255,255,255,opacity))
    watermarked = Image.alpha_composite(img, txt_layer)
    watermarked.convert('RGB').save(output_path, 'PNG')
    return output_path
