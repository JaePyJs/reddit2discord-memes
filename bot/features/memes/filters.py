from PIL import Image, ImageEnhance, ImageFilter

def apply_filter(img, filter_name):
    """
    Apply a named filter to the image.
    Supported: grayscale, blur, sharpen, contrast, brightness, edge_enhance
    """
    if filter_name == 'grayscale':
        return img.convert('L').convert('RGBA')
    elif filter_name == 'blur':
        return img.filter(ImageFilter.GaussianBlur(3))
    elif filter_name == 'sharpen':
        return img.filter(ImageFilter.SHARPEN)
    elif filter_name == 'contrast':
        return ImageEnhance.Contrast(img).enhance(2.0)
    elif filter_name == 'brightness':
        return ImageEnhance.Brightness(img).enhance(1.5)
    elif filter_name == 'edge_enhance':
        return img.filter(ImageFilter.EDGE_ENHANCE)
    else:
        raise ValueError(f'Unknown filter: {filter_name}')

