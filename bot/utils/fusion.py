from PIL import Image

def fuse_images(img1_path, img2_path, output_path, alpha=0.5):
    """
    Blend two images together with the given alpha.
    alpha: 0.0 (only img1) to 1.0 (only img2)
    """
    img1 = Image.open(img1_path).convert('RGBA')
    img2 = Image.open(img2_path).convert('RGBA')
    img2 = img2.resize(img1.size)
    fused = Image.blend(img1, img2, alpha)
    fused.save(output_path)
    return output_path
