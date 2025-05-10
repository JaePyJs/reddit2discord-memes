from PIL import Image, ImageEnhance, ImageFilter

def deep_fry(img: Image.Image) -> Image.Image:
    # Increase contrast, saturation, and add noise
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.5)
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(2.5)
    img = img.filter(ImageFilter.SHARPEN)
    return img
