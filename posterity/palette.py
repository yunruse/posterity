"Palette interpreter."

from collections import namedtuple
from pathlib import Path

from PIL import Image


PaletteEntry = namedtuple('Color', ('symbol', 'rgb', 'name'))

class Palette(list[PaletteEntry]):
    @staticmethod
    def interpret_entry(string: str):
        "Interpret e.g. `r ff0000 Red`"
        symbol, hexcol, name = string.strip().split(maxsplit=2)
        assert len(symbol) == 1
        hexcol = hexcol.removeprefix('#')
        hexcol = [int(hexcol[i:i+2], base=16) for i in range(0, 6, 2)]
        return PaletteEntry(symbol, hexcol, name)

    @classmethod
    def from_file(cls, path: Path):
        self = cls()
        with open(path) as f:
            for line in f.readlines():
                line = line.strip().split('#', maxsplit=1)[0]
                if line:
                    self.append(self.interpret_entry(line))
        return self
    
    def __getitem__(self, symbol: str):
        for col in self:
            if col.symbol == symbol:
                return col
        raise KeyError('Palette does not contain symbol', symbol)
    
    def image(self):
        im = Image.new('P', (1, len(self)))
        im.putpalette(sum([c.rgb for c in self], start=[]))
        for i, col in enumerate(self):
            im.putpixel((0, i), tuple(col.rgb))
        return im