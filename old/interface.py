'''Editor interface, handling cropping, previews, and palette management.'''

from PIL import Image, ImageTk, ImageDraw
import re

import tkinter as tk
from tkinter import (
    filedialog as tkFile,
    messagebox as tkMsg,
    colorchooser as tkCol,
)

from tool import CanvasTool, bind, Toolkit
import xstitch

import interfaceStyle as iStyle

from crop import Crop

class Pencil(CanvasTool):
    def __init__(self, canvas, frameMaster, active=False):
        CanvasTool.__init__(self, canvas, frameMaster, active)

        self._colour = tk.StringVar(self.frame, value='000000')
        self._colour.trace('w', self.onColourType)
        
        # Grid
        f = self.frame
        r, c = f.grid_rowconfigure, f.grid_columnconfigure
        for col in (0, 2, 4):
            c(col, minsize=5)
        for col in (1, 3):
            c(col, weight=1, minsize=50)

        for row in (0, 2):
            r(row, minsize=5)

        lCol = tk.Label(f, anchor='e', text='Colour: #')
        lCol.grid(row=1, column=1, sticky='nes')

        self.entryColour = tk.Entry(f, width=7, textvariable=self._colour, font=iStyle.fontMono)
        self.entryColour.grid(row=1, column=3, sticky='news')

        bPicker = tk.Button(f, text='Colour picker...', command=self.onColourMenu)
        bPicker.grid(row=3, column=1, columnspan=3, sticky='news')

    def onColourMenu(self):
        rgb, hexl = tkCol.askcolor(color='#' + self._colour.get())
        self._colour.set(hexl[1:])

    def onColourType(self, *arg):
        col = self._colour.get()
        col = re.sub('[^0-9a-fA_F]', '', col).upper()
        if len(col) > 6:
            col = col[-6:]
        self._colour.set(col)
    
    @property
    def colour(self):
        return int(self._colour.get(), base=16)

    def getPixelCoordinate(self, x, y):
        bx1, by1, bx2, by2 = canvas.imageExtent
        
        if not (bx1 < x < bx2 and by1 < y < by2):
            return None, None
        
        wVis, hVis = bx2 - bx1, by2 - by1
        wImag, hImag = menu.imageEdited.size
        x2 = int((x - bx1) * wImag / wVis)
        y2 = int((y - by1) * hImag / hVis)
        return x2, y2
        
        
    @bind('<Button-1>')
    def drawStart(self, canvas, event, menu):
        x, y = self.getPixelCoordinate(event.x, event.y)
        if not x:
            return

        menu.draw.rectangle((x, y, x+2, y+2), fill=self.colour)
        canvas.redraw()
        self.lastDraw = x, y
        print(x, y)

    @bind('<B1-Motion>')
    def drawDrag(self, canvas, event, menu):
        x, y = self.getPixelCoordinate(event.x, event.y)
        if not x:
            return
        
        menu.draw.line((*self.lastDraw, x, y), fill=self.colour, width=1)
        canvas.redraw()
        self.lastDraw = x, y
        print(x, y)

class xsCanvas(tk.Canvas):
    def __init__(self, master):
        self.master = master
        tk.Canvas.__init__(self, bg='#333333', relief='ridge', bd=0)

        self.bind('<Configure>', lambda e: self.redraw(automatic=True))

        # initialised in onResize
        self.imagetk = None
        self.spaceOnSides = None
        self.prevSize = None

    def redraw(self, automatic=False):
        menu = self.master
        if not hasattr(menu, 'imageEdited'):
            # not loaded yet
            return
        
        # Disturb cropping as it is now incorrect coordinates

        menu.crop.start = None

        # Draw image
        self.delete('image')
        img = menu.imageEdited
        
        wCanv, hCanv = self.winfo_width(), self.winfo_height()
        
        if img is None or wCanv < 10 or hCanv == 10:
            return

        # Check if image doesn't need resizing
        if automatic and self.prevSize:
            wPrev, hPrev = self.prevSize
            if self.spaceOnSides and wPrev == wCanv or hPrev == hCanv:
                self._drawImage()
                return
        
        self.prevSize = wCanv, hCanv

        wImag, hImag = img.size
        if wImag == 0 or hImag == 0:
            return
        wProp, hProp = wCanv / wImag, hCanv / hImag

        # Ensure constant aspect ratio via proportion magic

        self.spaceOnSides = wProp > hProp
        if self.spaceOnSides:
            w, h = int(wImag * hProp), hCanv
        else:
            w, h = wCanv, int(hImag * wProp)
            
        # Store extent of image, so we know we've clicked on the image
        self.imageExtent = (
            (wCanv - w) // 2, (hCanv - h) // 2,
            (wCanv + w) // 2, (hCanv + h) // 2)

        # Ensure pixels are not blurred
        method = Image.BILINEAR if w < wImag else Image.NEAREST
        
        self.imageResized = img.resize((w, h), method)
        self.imagetk = ImageTk.PhotoImage(self.imageResized)

        menu.crop.lSizeVisual.config(
            text=f'Visual: {w:>4}×{h:<4}')
        self._drawImage()

    def _drawImage(self):
        wCanv, hCanv = self.winfo_width(), self.winfo_height()
        w, h = self.imageResized.size
        
        self.imageExtent = (
            (wCanv - w) // 2, (hCanv - h) // 2,
            (wCanv + w) // 2, (hCanv + h) // 2)
        self.create_image(
            wCanv // 2, hCanv // 2, anchor='center',
            image=self.imagetk, tags='image')

class xsEditor(tk.Frame):
    def __init__(self, menu):
        self.master = menu
        tk.Frame.__init__(self, width=200)

        # Grid configuration
        r, c = self.grid_rowconfigure, self.grid_columnconfigure
        for col in (0, 2, 4):
            c(col, minsize=5)
        for col in (1, 3):
            c(col, weight=1, minsize=50)

        for row in (0, 2, 4, 6):
            r(row, minsize=5)

        def label(row, name, **kwargs):
            label = tk.Label(self, anchor='w', font=fontMono, **kwargs)
            label.grid(row=row, column=1, columnspan=3, sticky='news')
            setattr(self, name, label)

        label(1, 'lSize')
        label(3, 'lSizeCropped')
        self.bCrop = tk.Button(
            self, text='Reset crop...', command=menu.crop.resetCrop, state='disabled')
        self.bCrop.grid(row=5, column=1, columnspan=3, sticky='news')

        label(7, 'lSizeVisual')

class MenuBar(tk.Menu):
    def __init__(self, master):
        tk.Menu.__init__(self, master)

    FILETYPES = (
        ('Image', '*.png;*.jpeg;*.jpg;*.gif;*.tiff;*.bmp'),
        ('All files', '*.*'),
        )

    def openFile(self):
        fpath = tkFile.askopenfilename(filetypes=self.FILETYPES)
        if fpath:
            self.master.loadImage(fpath)
    
class xsInterface(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title('Xstitch')
        self.minsize(600, 400)

        self.grid_columnconfigure(1, weight=1, minsize=200)
        self.grid_columnconfigure(2, weight=0, minsize=200)

        self.grid_rowconfigure(1, weight=0, minsize=32)
        self.grid_rowconfigure(2, weight=1, minsize=180)

        # Canvas
        
        self.canvas = xsCanvas(self)
        self.canvas.grid(column=1, row=2, sticky='news')

        # Main sidebar

        self.sidebar = tk.Frame(self, width=200)
        self.sidebar.grid(column=2, row=1, rowspan=2, sticky='news')

        # Tools

        self.toolkit = Toolkit(self, bg='#666666')
        self.toolkit.grid(column=1, row=1, sticky='news')
        
        self.crop = Crop(self.canvas, self.sidebar)
        self.toolkit.append(self.crop, icon='crop.gif', text='Crop', active=True)

        self.pencil = Pencil(self.canvas, self.sidebar)
        self.toolkit.append(self.pencil, icon='crop.gif', text='Pencil')

        # Image attributes

        self.palette = xstitch.Palette.fromFile('palette.txt')

        # Original as loaded
        self.filepath = None
        self.imageOrig = None

        # As edited
        self.imageEdited = None
        self.draw = None

    def loadImage(self, fpath):
        self.filepath = fpath
        self.imageOrig = Image.open(fpath)
        self.crop.resetCrop()

if __name__ == '__main__':
    self = xsInterface()
    menu = self
    canvas = menu.canvas
    self.loadImage('in.png')
