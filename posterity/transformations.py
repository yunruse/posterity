from PIL import Image
from .palette import Palette

def remove_gutter(im: Image, gutter: int):
    "Remove gutter% of pixels from edges."
    w, h = im.size
    g = min(w, h) * gutter/100
    return im.crop((g, g, w-g, h-g))


def resize(im: Image, size: tuple[int, int]):
    "Resize, cropping if aspect ratios differ."
    w, h = im.size
    aspect = w/h
    W, H = size
    desired_aspect = W / H
    
    if desired_aspect == aspect:
        # source is ok aspect
        return im.resize(size)
    
    if aspect > desired_aspect:
        # source is too wide
        w2 = h * desired_aspect
        x0 = (w - w2) // 2
        im = im.crop((x0, 0, w-x0, h))
    
    if aspect < desired_aspect:
        # source is too tall
        h2 = w / desired_aspect
        y0 = (h - h2) // 2
        im = im.crop((0, y0, w, h-y0))

    return im.resize(size)


def posterize(im: Image, pal: Palette):
    pal.image().save('pal.png')
    return im.quantize(palette=pal.image())