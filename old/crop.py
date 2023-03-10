import tkinter as tk

from PIL import Image, ImageDraw

from tool import CanvasTool, bind, Toolkit
import interfaceStyle as iStyle

class Crop(CanvasTool):
    '''Handler for canvas size changes.'''
    def __init__(self, widget, frameMaster, active=False):
        CanvasTool.__init__(self, widget, frameMaster, active)
        self.start = None
        self.hasCropped = False
        self.boundary = None

        f = self.frame

        # Grid configuration
        r, c = f.grid_rowconfigure, f.grid_columnconfigure
        for col in (0, 2, 4):
            c(col, minsize=5)
        for col in (1, 3):
            c(col, weight=1, minsize=50)

        for row in (0, 2, 4, 6):
            r(row, minsize=5)

        def label(row, name, **kwargs):
            label = tk.Label(f, anchor='w', font=iStyle.fontMono, **kwargs)
            label.grid(row=row, column=1, columnspan=3, sticky='news')
            setattr(self, name, label)

        label(1, 'lSize')
        label(3, 'lSizeCropped')
        self.bCrop = tk.Button(
            f, text='Reset crop...', command=self.resetCrop, state='disabled')
        self.bCrop.grid(row=5, column=1, columnspan=3, sticky='news')

        label(7, 'lSizeVisual')

    def onSizeChange(self):
        canvas = self.widget
        menu = canvas.master
        w1, h1 = menu.imageOrig.size
        w2, h2 = menu.imageEdited.size
        self.lSize.config(
            text=f'Size:  {w1:>4}×{h1:<4}')
        self.lSizeCropped.config(
            text=f'Crop:  {w2:>4}×{h2:<4}')

        canvas.redraw()

    @bind('<Button-3>')
    def resetCrop(self, *args):
        self.boundary = None
        canvas = self.widget
        menu = canvas.master
        self.bCrop.config(state='disabled')
        menu.imageEdited = menu.imageOrig.copy()
        menu.draw = ImageDraw.Draw(menu.imageEdited)
        self.onSizeChange()
    
    @bind('<Button-1>')
    def cropEventStart(self, canvas, event, menu):
        self.start = (event.x, event.y)
        self.bCrop.config(text='Cropping...', state='disabled')

    @bind('<B1-Motion>')
    def cropEventPreview(self, canvas, event, menu):
        canvas.delete('cropIndicator')
        x1, y1 = self.start
        x2, y2 = event.x, event.y

        x1, x2 = sorted((x1, x2))
        y1, y2 = sorted((y1, y2))
        bx1, by1, bx2, by2 = canvas.imageExtent

        x1, x2 = max(x1, bx1), min(x2, bx2)
        y1, y2 = max(y1, by1), min(y2, by2)
        w, h = canvas.winfo_width(), canvas.winfo_height()

        # use negative space to show what'll be excluded from crop,
        # with a cool aperture effectf
        for args in (
            (x1, 0, w, y1),   # above crop
            (0, y2, x2, h),   # below crop
            (0, 0, x1, y2), # left of crop
            (x2, y1, w, h), # right of crop
            ):
            canvas.create_rectangle(
                *args, outline='#333333', width=1, fill='gray',
                stipple='gray50', tags='cropIndicator')

    @bind('<ButtonRelease-1>')
    def cropEventEnd(self, canvas, event, menu):
        canvas.delete('cropIndicator')
        
        state = ['active', 'disabled'][self.hasCropped and self.start is None]
        self.bCrop.config(text='Reset crop...', state=state)
        
        if self.start is None:
            # was resized mid-crop
            return
        
        self.hasCropped = True

        # Get crop coordinates
        
        x1, y1 = self.start
        x2, y2 = event.x, event.y

        x1, x2 = sorted((x1, x2))
        y1, y2 = sorted((y1, y2))
        
        # Ensure crop doesn't extend out of image
        bx1, by1, bx2, by2 = canvas.imageExtent
        wVis, hVis = bx2 - bx1, by2 - by1
        wImag, hImag = menu.imageEdited.size
        
        # normalise to image coordinates
        x1 = int(max(x1 - bx1, 0)    * wImag / wVis)
        x2 = int(min(x2 - bx1, wVis) * wImag / wVis)
        y1 = int(max(y1 - by1, 0)    * hImag / hVis)
        y2 = int(min(y2 - by1, hVis) * hImag / hVis)

        self.boundary = (x1, y1, x2, y2)
        cropped = menu.imageEdited.crop(self.boundary)
    
        w, h = cropped.size

        if w and h:
            menu.imageEdited = cropped
            self.onSizeChange()
