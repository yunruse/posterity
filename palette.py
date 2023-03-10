import math
import re

from PIL import Image

_symbol = '(?:(.) )?#'
_hex = '([0-9a-fA-F]{2})'
_name = '(?: ([a-zA-Z ]+))?'
re_entry = re.compile(_symbol + _hex*3 + _name)

def read_palette_file(string: str):
    table = [] # [r, g, b, ...]
    mapping = {} # {(r, g, b): (symbol, name)}
    for symbol, *rgb, name in re_entry.findall(string):
        rgb = [int(i, base=16) for i in rgb]
        table += rgb
        mapping[tuple(rgb)] = (symbol, name)
    return table, mapping

def repeat(list_like, length: int) -> list:
    '''Repeat list until it is of a certain length, clipping if needed'''
    ll = list(list_like)
    l = len(ll)
    return (ll * math.ceil(length / l))[:length]

class Palette(dict):
    __slots__ = '_image'.split()

    def _update_palette(self, rgb=None):
        if rgb is None:
            rgb = []
            for r, g, b in self.keys():
                rgb += [r, g, b]
        self._image.putpalette(repeat(rgb, 256 * 3))
    
    def __init__(self, mapping=None, force_table=None):
        dict.__init__(self, mapping or {})
        self._image = Image.new('P', (16, 16))
        self._update_palette(force_table)

    def __setitem__(self, rgb, info):
        if not (isinstance(rgb, tuple) and len(rgb) == 3
                and all(isinstance(i, int) for i in rgb)):
            raise ValueError('RGB must be tuple(int, int, int)')
        
        dict.__setitem__(self, rgb, info)
        self._update_palette()

    @classmethod
    def fromFile(cls, file_name):
        with open(file_name) as f:
            table, mapping = read_palette_file(f.read(-1))
            return cls(mapping, table)

    def quantize(self, image, dither=True):
        if image.mode not in ("RGB", 'L'):
            raise ValueError(
                'only RGB or L mode images can be quantized to a palette')
        im = image.im.convert('P', int(dither), self._image.im)

        # Pillow > 4.0 has ._new
        try:
            return image._new(im)
        except AttributeError:
            return image._makeself(im)

# Main script generates evenly through RGB cube

def generate_pallete(step):
    if 255 % step:
        raise ValueError('255 does not divide by {}'.format(step))
    c = range(0, 255+step, step)
    for r in c:
        for g in c:
            for b in c:
                yield r, g, b

if __name__ == '__maine__':
    step = 0x33
    print('Generating colour list in steps of 0x{:02x}...'.format(step))
    with open('palette-stepped.txt', 'w') as f:
        for r, g, b in generate_pallete(step):
            hex_line = '#{:02x}{:02x}{:02x}'.format(r, g, b)
            f.write(hex_line + '\n')

if __name__ == '__main__':
    pal = Palette.fromFile('palette.txt')
