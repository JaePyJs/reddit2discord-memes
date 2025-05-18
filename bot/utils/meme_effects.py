from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import io
import random
import math
import numpy as np

# Dictionary of available effects
EFFECTS = {
    'deep-fry': 'Intense saturation, contrast and noise like deep-fried memes',
    'vaporwave': 'Retro 80s/90s aesthetic with purple/blue tint',
    'jpeg': 'Add JPEG compression artifacts',
    'glitch': 'Digital glitch effect with color shifts',
    'grayscale': 'Convert image to black and white',
    'invert': 'Invert all colors in the image',
    'blur': 'Apply a soft blur effect',
    'pixelate': 'Reduce resolution for a pixelated look',
    'sepia': 'Old-fashioned brownish tone'
}

def list_effects():
    """Return a dictionary of available effects with descriptions"""
    return EFFECTS

def apply_effect(img: Image.Image, effect_name: str) -> Image.Image:
    """Apply the specified effect to the image"""
    if not effect_name or effect_name.lower() == 'none':
        return img
    
    effect_name = effect_name.lower()
    
    if effect_name == 'deep-fry':
        return deep_fry(img)
    elif effect_name == 'vaporwave':
        return vaporwave(img)
    elif effect_name == 'jpeg':
        return jpeg_artifact(img)
    elif effect_name == 'glitch':
        return glitch(img)
    elif effect_name == 'grayscale':
        return img.convert('L').convert('RGB')
    elif effect_name == 'invert':
        return ImageOps.invert(img)
    elif effect_name == 'blur':
        return img.filter(ImageFilter.GaussianBlur(radius=3))
    elif effect_name == 'pixelate':
        return pixelate(img)
    elif effect_name == 'sepia':
        return sepia(img)
    else:
        return img  # Return original if effect not found

def deep_fry(img: Image.Image) -> Image.Image:
    """Deep fried meme effect with heavy saturation, contrast and noise"""
    # Increase contrast and saturation
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.5)
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(2.5)
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.2)
    
    # Add noise and artifacts
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    
    # Add slight JPEG artifacts for that "repeatedly saved" look
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=15)
    buffer.seek(0)
    img = Image.open(buffer)
    
    return img

def vaporwave(img: Image.Image) -> Image.Image:
    """Vaporwave aesthetic with purple/blue color shift"""
    # Split the image into RGB channels
    r, g, b = img.split()
    
    # Enhance the blue and red channels
    enhancer = ImageEnhance.Brightness(b)
    b = enhancer.enhance(1.2)
    enhancer = ImageEnhance.Brightness(r)
    r = enhancer.enhance(1.1)
    
    # Merge channels with subtle shift
    img = Image.merge("RGB", (r, g, b))
    
    # Apply color overlay
    overlay = Image.new('RGB', img.size, (221, 160, 221))  # Purple/pink tone
    img = Image.blend(img, overlay, 0.3)
    
    # Add glow effect
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)
    
    return img

def jpeg_artifact(img: Image.Image) -> Image.Image:
    """Add JPEG compression artifacts"""
    # Save with very low quality to create artifacts
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=5)
    buffer.seek(0)
    return Image.open(buffer)

def glitch(img: Image.Image) -> Image.Image:
    """Create digital glitch effect with color channel shifts"""
    width, height = img.size
    img_array = np.array(img)
    
    # RGB channel shift
    r_shift = random.randint(-20, 20)
    g_shift = random.randint(-20, 20)
    b_shift = random.randint(-20, 20)
    
    # Create random glitch regions
    num_glitches = random.randint(5, 15)
    for _ in range(num_glitches):
        # Random horizontal slice
        y_pos = random.randint(0, height - 10)
        h_slice = random.randint(5, 20)
        x_shift = random.randint(-15, 15)
        
        # Apply shift to slice
        if 0 <= y_pos < height and 0 <= y_pos + h_slice < height:
            # Shift slice horizontally
            slice_data = img_array[y_pos:y_pos + h_slice, :].copy()
            if x_shift > 0:
                img_array[y_pos:y_pos + h_slice, x_shift:] = slice_data[:, :-x_shift]
            elif x_shift < 0:
                img_array[y_pos:y_pos + h_slice, :x_shift] = slice_data[:, -x_shift:]
    
    # Apply RGB shifts to whole image
    result = Image.new('RGB', (width, height))
    r, g, b = img.split()
    
    # Shift red channel
    r_data = np.array(r)
    if r_shift > 0:
        r_data = np.roll(r_data, r_shift, axis=1)
    
    # Shift green channel
    g_data = np.array(g)
    if g_shift > 0:
        g_data = np.roll(g_data, g_shift, axis=1)
    
    # Shift blue channel
    b_data = np.array(b)
    if b_shift > 0:
        b_data = np.roll(b_data, b_shift, axis=1)
    
    # Merge channels
    r = Image.fromarray(r_data)
    g = Image.fromarray(g_data)
    b = Image.fromarray(b_data)
    result = Image.merge('RGB', (r, g, b))
    
    return result

def pixelate(img: Image.Image) -> Image.Image:
    """Pixelate the image by reducing and then increasing resolution"""
    small_size = (img.width // 10, img.height // 10)
    return img.resize(small_size, Image.NEAREST).resize(img.size, Image.NEAREST)

def sepia(img: Image.Image) -> Image.Image:
    """Apply sepia tone effect"""
    # Convert to sepia tone
    img = img.convert('RGB')
    
    # Apply sepia transformation
    data = np.array(img)
    r, g, b = data[:,:,0], data[:,:,1], data[:,:,2]
    
    # Apply sepia tone formula
    tr = 0.393 * r + 0.769 * g + 0.189 * b
    tg = 0.349 * r + 0.686 * g + 0.168 * b
    tb = 0.272 * r + 0.534 * g + 0.131 * b
    
    # Ensure values are within range
    tr = np.clip(tr, 0, 255)
    tg = np.clip(tg, 0, 255)
    tb = np.clip(tb, 0, 255)
    
    # Create new array and make image
    data = np.stack([tr, tg, tb], axis=2).astype('uint8')
    return Image.fromarray(data)