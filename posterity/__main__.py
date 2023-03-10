"Pixel-and-posterize tool."

from argparse import ArgumentParser

from PIL import Image

from .palette import Palette
from .transformations import *

def transform(args):
    im = Image.open(args.image)
    if args.palette:
        im = posterize(
            im, Palette.from_file(args.palette))
    if args.gutter:
        im = remove_gutter(im, args.gutter)
    if args.size:
        im = resize(im, args.size)
    return im

if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__)

    parser.add_argument(
        'image', help="The path to the image.")

    tools = parser.add_argument_group('tools', 'Applied in order.')
    
    parser.add_argument(
        '--palette', '-p',
        help="Quantize colors to a palette.txt file.")
    tools.add_argument(
        '--gutter', '-g', type=int, default=None,
        help="Remove G%% of pixels from all edge.")
    tools.add_argument(
        '--square', '-S', type=int, default=None,
        help="Square shorthand for --size")
    tools.add_argument(
       '--size', '-s', type=int, nargs=2, default=None,
        help="Resize to width and height.")

    def interpret(args):
        if args.square:
            args.size = (args.square, args.square)
            del args.square
        return args

    args = interpret(parser.parse_args())
    im = transform(args)
    im.save('foo.png')