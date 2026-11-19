"""Plain borderless window that covers the recording stage (kept just below the demo windows)."""
import ctypes
import sys
import tkinter as tk

ctypes.windll.user32.SetProcessDPIAware()
x, y, w, h, color = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
root = tk.Tk()
root.overrideredirect(True)
root.geometry("%dx%d+%d+%d" % (w, h, x, y))
root.configure(bg=color)
root.attributes("-topmost", True)
if len(sys.argv) < 7 or sys.argv[6] != "keep":
    root.after(800, lambda: root.attributes("-topmost", False))
root.mainloop()
