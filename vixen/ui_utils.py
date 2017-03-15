"""Some UI utilities.

This module was created to make it easy to ask the user for a filename or
directory. It is surprisingly hard to do this on a browser so we resort to
using Tkinter for this task.

"""
import os
import subprocess
import sys
try:
    import Tkinter as tkinter
    import tkFileDialog as FD
except ImportError:  # pragma: no cover
    import tkinter
    import tkinter.filedialog as FD


def _make_root():
    """This creates a Tkinter root and raises the window. Otherwise the window
    shows up at the bottom. Taken from here:

    http://stackoverflow.com/questions/3375227/how-to-give-tkinter-file-dialog-focus

    """
    root = tkinter.Tk()
    root.withdraw()

    # Make it almost invisible - no decorations, 0 size, top left corner.
    root.overrideredirect(True)
    root.geometry('0x0+0+0')

    # Show window again and lift it to top so it can get focus,
    # otherwise dialogs will end up behind the terminal.
    root.deiconify()
    root.lift()
    root.focus_force()
    if sys.platform == 'darwin':
        tmpl = 'tell application "System Events" to set frontmost '\
               'of every process whose unix id is {} to true'
        script = tmpl.format(os.getpid())
        subprocess.check_call(['/usr/bin/osascript', '-e', script])
        root.update()
    elif sys.platform.startswith('win'):
        root.attributes('-topmost', True)
        root.lift()
        root.after(0, lambda: root.attributes('-topmost', False))

    return root


def askopenfilename(title=None, **options):
    root = _make_root()
    result = FD.askopenfilename(parent=root, title=title, **options)
    root.destroy()
    return result


def askdirectory(title=None, **options):
    root = _make_root()
    result = FD.askdirectory(parent=root, title=title, **options)
    root.destroy()
    return result


def asksaveasfilename(title=None, **options):
    root = _make_root()
    result = FD.asksaveasfilename(parent=root, title=title, **options)
    root.destroy()
    return result
