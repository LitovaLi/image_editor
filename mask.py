import tkinter
from tkinter import *
from PIL import Image, ImageGrab, ImageTk
import os.path

class Paint(object):

    DEFAULT_PEN_SIZE = 5.0
    DEFAULT_COLOR = 'white'

    def __init__(self, temp_dir):
        self.root = tkinter.Toplevel()
        frame = Frame(self.root)
        frame.grid()
        self.temp_dir = temp_dir

        self.pen_button = Button(frame, text='Карандаш', command=self.use_pen)
        self.pen_button.grid(row=0, column=0)

        self.rectangle_button = Button(frame, text='Прямоугольник', command=self.use_rectangle)
        self.rectangle_button.grid(row=0, column=1)

        self.save_button = Button(frame, text='Сохранить маску', command=self.save_mask)
        self.save_button.grid(row=0, column=2)

        self.choose_size_button = Scale(frame, from_=1, to=10, orient=HORIZONTAL)
        self.choose_size_button.grid(row=0, column=4)

        image = Image.open("images/bird_impaint2.jpg")
        photo = ImageTk.PhotoImage(image)
        self.c = Canvas(frame, bg="white", width=photo.width(), height=photo.height())
        self.c.create_image(0, 0, anchor='nw', image=photo)
        self.c.grid(row=1, columnspan=5)

        self.setup()
        self.root.mainloop()

    def setup(self):
        self.old_x = None
        self.old_y = None
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.x = self.y = 0
        self.line_width = self.choose_size_button.get()
        self.color = self.DEFAULT_COLOR
        self.active_button = self.pen_button
        self.c.bind('<B1-Motion>', self.paint)
        self.c.bind('<ButtonRelease-1>', self.reset)

    def use_pen(self):
        self.activate_button(self.pen_button)
        self.c.unbind("<ButtonPress-1>")
        self.c.unbind("<B1-Motion>")
        self.c.unbind("<ButtonRelease-1>")
        self.c.bind('<B1-Motion>', self.paint)
        self.c.bind('<ButtonRelease-1>', self.reset)

    def use_rectangle(self):
        self.activate_button(self.rectangle_button)
        self.c.unbind('<B1-Motion>')
        self.c.unbind('<ButtonRelease-1>')
        self.c.bind("<ButtonPress-1>", self.on_button_press)
        self.c.bind("<B1-Motion>", self.on_move_press)
        self.c.bind("<ButtonRelease-1>", self.on_button_release)

    def use_save_button(self):
        self.activate_button(self.save_button)

    def activate_button(self, some_button):
        self.active_button.config(relief=RAISED)
        some_button.config(relief=SUNKEN)
        self.active_button = some_button

    def paint(self, event):
        self.line_width = self.choose_size_button.get()
        if self.old_x and self.old_y:
            self.c.create_line(self.old_x, self.old_y, event.x, event.y,
                               width=self.line_width, fill=self.color,
                               capstyle=ROUND, smooth=TRUE, splinesteps=36)
        self.old_x = event.x
        self.old_y = event.y

    def on_button_press(self, event):
        # save mouse drag start position
        self.start_x = event.x
        self.start_y = event.y

        # create rectangle if not yet exist
        # if not self.rect:
        if self.active_button == self.rectangle_button:
            self.rect = self.c.create_rectangle(self.x, self.y, 1, 1, fill=self.color, width=0)

    def on_move_press(self, event):
        curX, curY = (event.x, event.y)

        # expand rectangle as you drag the mouse
        self.c.coords(self.rect, self.start_x, self.start_y, curX, curY)

    def on_button_release(self, event):
        pass

    def reset(self, event):
        self.old_x, self.old_y = None, None

    def save_mask(self):
        ImageGrab.grab(bbox=(
            self.c.winfo_rootx(),
            self.c.winfo_rooty(),
            self.c.winfo_rootx() + self.c.winfo_width(),
            self.c.winfo_rooty() + self.c.winfo_height()
        )).save(os.path.join(self.temp_dir, "mask.jpg"))

    def _close(self):
        self.root.quit()
