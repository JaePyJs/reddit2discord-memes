from PIL import Image
import os

def optimize_image(input_path, output_path, quality=85, max_size=(1024, 1024)):
    """
    Optimize the image for faster processing and smaller file size.
    - quality: JPEG/PNG quality (1-100)
    - max_size: resize if larger than this
    """
    img = Image.open(input_path)
    img.thumbnail(max_size, Image.ANTIALIAS)
    ext = os.path.splitext(output_path)[1].lower()
    if ext in ['.jpg', '.jpeg']:
        img = img.convert('RGB')
        img.save(output_path, 'JPEG', quality=quality, optimize=True)
    else:
        img.save(output_path, 'PNG', optimize=True)
    return output_path
