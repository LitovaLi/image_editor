import tkinter
from tkinter import *
from PIL import Image, ImageGrab, ImageTk
import os.path
from tkinter import messagebox as mb

class Paint(object):

    DEFAULT_PEN_SIZE = 5.0
    DEFAULT_COLOR = 'white'

    def __init__(self, temp_dir, image, id_temp):
        self.root = tkinter.Toplevel()
        self.root.title("Создание маски")
        self.temp_dir = temp_dir
        self.id_temp = id_temp

        self.pen_button = Button(self.root, text='Карандаш', command=self.use_pen)
        self.pen_button.grid(row=0, column=0)

        self.rectangle_button = Button(self.root, text='Прямоугольник', command=self.use_rectangle)
        self.rectangle_button.grid(row=0, column=1)

        self.color_button = Button(self.root, text='Белый/Черный', command=self.choose_color)
        self.color_button.grid(row=0, column=2)

        self.save_button = Button(self.root, text='Сохранить маску', command=self.use_save_button)
        self.save_button.grid(row=0, column=4)

        self.help = Label(self.root, text="Объекты для удаления закрасьте белым \n"
                                          "Остальные светлые участки - черным")
        self.help.grid(row=0, column=6)

        self.choose_size_button = Scale(self.root, from_=1, to=20, orient=HORIZONTAL)
        self.choose_size_button.grid(row=0, column=7)

        # self.image = Image.open(image_path)
        self.image = Image.fromarray(image)
        self.photo = ImageTk.PhotoImage(self.image)
        self.c = Canvas(self.root, bg="white", width=self.photo.width(), height=self.photo.height(), borderwidth=0)
        self.c.create_image(0, 0, anchor='nw', image=self.photo)
        self.c.grid(row=1, columnspan=8)

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

    def choose_color(self):
        #Simulate pushing the button
        self.color_button.config(relief=SUNKEN)
        self.color_button.after(200, lambda: self.color_button.config(relief=RAISED))
        if self.color == 'white':
            self.color = 'black'
        else:
            self.color = 'white'

    def use_save_button(self):
        self.save_button.config(relief=SUNKEN)
        self.save_button.after(200, lambda: self.save_button.config(relief=RAISED))
        self.save_mask()

    def activate_button(self, some_button):
        self.active_button.config(relief=RAISED)
        some_button.config(relief=SUNKEN)
        self.active_button = some_button

    def use_help_button(self):
        self.help_button.config(relief=SUNKEN)
        self.help_button.after(200, lambda: self.help_button.config(relief=RAISED))
        mb.showinfo("Информация", "Объекты, которые хотите удалить, закрасьте белым цветом. \n"
                                  "Все светлые участки на изображении закрасьте черным")

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
            self.c.winfo_rootx() + self.photo.width(),
            self.c.winfo_rooty() + self.photo.height(),
        )).save(os.path.join(self.temp_dir, self.id_temp + "_mask.png"))
        mb.showinfo("Сохранение", "Маска успешно сохранена")
        self.root.destroy()

    def _close(self):
        self.root.quit()
