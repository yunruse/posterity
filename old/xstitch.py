'''Cross-stitchifier'''

import itertools

from PIL import Image, ImageDraw, ImageOps
from palette import Palette

class CrossStitch:
    '''Factory that turns a picture and palette into a cross-stitch pattern.'''
    
    def __init__(self, img, palette, minimum_size=100, dither=False, resample=Image.BICUBIC):
        '''Pixellate and solarize to palette.'''
        self.palette = palette
        # Pixellate down
        w, h = img.size
        s = minimum_size / min(w, h)
        sizeSmall = int(w * s), int(h * s)

        self.pixel = img.resize(sizeSmall, resample=resample)
        self.quant = self.palette.quantize(self.pixel, dither=dither)

    def _symbolGenerator(self):
        symbols = [self.palette[rgb][0] for rgb in self.palette]
        w, h = self.quant.size
        for x in range(w):
            for y in range(h):
                index = self.quant.getpixel((x, y))
                yield x, y, symbols[index]

    def _symbolMask(self, pixel_size=16, grid_width=1):
        '''Generate font symbols'''
        
        sizeLarge = tuple(i * pixel_size for i in self.quant.size)
        
        mask = Image.new('L', sizeLarge, 0)
        draw = ImageDraw.Draw(mask)

        w, h = self.quant.size
        for x, y, symbol in self._symbolGenerator():
            x_ = x * pixel_size  + pixel_size //2
            y_ = y * pixel_size  + 4
            draw.text((x_, y_), symbol, fill=255)

        if grid_width:
            w2, h2 = mask.size
            for x in range(1, w):
                x *= pixel_size
                draw.line((x, 0, x, h2), fill=255, width=grid_width)
            for y in range(1, h):
                y *= pixel_size
                draw.line((0, y, w2, y), fill=255, width=grid_width)
            
        return mask

    def keyRealColor(self, pixel_size=16, grid_width=1):
        '''Draw a guide with real-colour pixels and semi-transparent guide'''
        
        mask = self._symbolMask(pixel_size, grid_width)
        large = self.quant.resize(mask.size, resample=Image.NEAREST)
        
        # 'key' layer is the colouring of the guide symbols:
        # a little brighter, or darker if already bright enough
        keypalette = []
        brighten_by = int(255 * 0.2)
        lim = 255 - brighten_by
        q = lambda i, f: min(max(i + f, 0), 255)
        for r, g, b in self.palette:
            f = brighten_by
            if r > lim or g > lim or b > lim:
                f *= -1 # Too bright, darken
            keypalette += [q(r,f), q(g,f), q(b,f)]

        key = large.copy()
        key.putpalette(keypalette)

        large = large.convert('RGB')
    
        return Image.composite(key, large, mask)

    def keyGrid(self, pixel_size=16, grid_width=2):
        
        return ImageOps.invert(self._symbolMask(pixel_size, grid_width))

if __name__ == '__main__':
    pal = Palette.fromFile('palette.txt')
    img = Image.open('in.png')
    stitch = CrossStitch(img, pal, minimum_size=40, dither=False)
    stitch.keyRealColor(16).save('realcolor.png')
    stitch.keyGrid(15).save('grid.png')
    draw = ImageDraw.Draw(stitch.pixel)
