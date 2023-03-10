'''Toolkit for hotswappable tkinter bindings'''
import functools

import tkinter as tk

def attributes(obj):
    for name in dir(obj):
        yield name, getattr(obj, name)

def bind(*sequences, bindToAll=False):
    '''Bind an event function in a Tool() object, using standard Tk sequences.'''
    def wrapped(f):
        f.__binding__ = (bindToAll, sequences)
        return f
    return wrapped

class Tool:
    '''
    Base class for a hot-swappable set of bindings for a widget.

    Useful for switching control schemes or tools for advanced bindings.
    
        class ClickSaysHi(Tool):
            @bind('<Button-1>')
            def sayHi(self, event):
                assert type(self) is not ClickSaysHi
                print(f'Hi from {type(self)} at {event.x}, {event.y}')

        root = tk.Tk()
        widget = tk.Canvas(root)
        sayHi = ClickSaysHi(widget, setName='clicking', active=True)

    Use stateful activation, but no promises another Tool hasn't
    hasn't overwritten all your bindings!
    
        sayHi.active = True

    As the class is simply a wrapper for convenience, 'self'
    is wrapped to be the widget you apply the toolkit on.
    So now if you left-click, you'd see:

        Hi from <class 'tkinter.Canvas'>: at 24, 100!
    
    '''
    
    __slots__ = 'widget bindings'.split()
    def __init__(self, widget, active=False):
        '''Create new tool.

        exclusiveBindings will remove ALL bindings before activation - otherwise
        they will just overwrite.
        To avoid confusion, make sure toolsets have empty functions for each binding.'''
        self.widget = widget
        
        # You'd think storing a mapping on the class would make
        # sense, but @decorators can only see the unbound function,
        # so there's no way to access the function.
        # So for a hacky workaround we use @bind to set a flag
        
        getFunc = lambda name: getattr(type(self), name)
        
        self.bindings = []

        possible_new_methods = set(dir(self)) - set(dir(Tool))
        
        for name in possible_new_methods:
            # Get class method so 'self' is unbound
            f = getattr(type(self), name, None)
            
            if f is None:
                continue
            
            info = getattr(f, '__binding__', None)
            if info is None:
                continue
            
            bindToAll, sequences = info
            func = self.modify_binding(f)
            self.bindings.append((func, bindToAll, sequences))

        self._active = False
        if active:
            self.activate()

    def modify_binding(self, f):
        '''Modifies unbound f when instantiating tool'''
        @functools.wraps(f)
        def let_me_introduce_my_self(e):
            f(self.widget, e) # convince function 'self' is actually the widget
        return let_me_introduce_my_self

    def activate(self):
        if self._active:
            return
        self._active = True
            
        for func, bindToAll, sequences in self.bindings:
            b = self.widget.bind_all if bindToAll else self.widget.bind
            for s in sequences:
                b(s, func)

    def deactivate(self):
        if not self._active:
            return
        self._active = False
            
        for func, bindToAll, sequences in self.bindings:
            b = tk.Canvas.unbind_all if bindToAll else self.widget.unbind
            for s in sequences:
                b(s)

    @property
    def active(self):
        return self._active

    @active.setter
    def _active_set(self, new):
        if new:
            self.activate()
        else:
            self.deactivate()

class CanvasTool(Tool):
    '''Tool that holds its own frame of settings'''
    def __init__(self, widget, frameMaster, active=False):
        self.frame = tk.Frame(frameMaster)
        self.frame.grid(row=0, column=0, sticky='news')
        self.frame.grid_remove()
        
        Tool.__init__(self, widget, active)
        
    def modify_binding(self, f):
        def modified(event):
            f(self, self.widget, event, self.widget.master)
        return modified

    def activate(self):
        Tool.activate(self)
        self.frame.grid()

    def deactivate(self):
        Tool.deactivate(self)
        self.frame.grid_remove()

class Toolkit(tk.Frame):
    def __init__(self, master, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)
        self.tools = []

    def resetTools(self):
        for tool, btn in self.tools:
            tool.deactivate()
            btn.config(relief='raised', bg='#F0F0F0')

    def append(self, tool, icon=None, text='', active=False):
        if isinstance(icon, str):
            icon = tk.PhotoImage(file=icon)
    
        btn = tk.Button(
            self, image=icon, text=text, compound='top',
            width=48, height=48, font=('Segoe UI', 8))
        
        def onClick():
            self.resetTools()
            tool.activate()
            btn.config(relief='sunken', bg='#cccccc')

        btn.config(command=onClick)
        
        btn.image = icon
        btn.pack(side='left')
        self.tools.append((tool, btn))

        if active:
            onClick()


if __name__ == '__main__':
    from interface import xsInterface
    self = xsInterface()
    menu = self
    self.loadImage('in.png')
