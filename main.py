import os.path
from tkinter import *
from tkinter import filedialog as fd
from tkinter.ttk import Notebook
from tkinter import messagebox as mb
import cv2
import numpy as np
import json
from image_info import ImageInfo
from optional_pane import EnhanceSliderWindow
import tempfile
import shutil
import random


CONFIG_FILE = "config.json"


class PyPhotoEditor:
    def __init__(self):
        self.root = Tk()
        self.image_tabs = Notebook(self.root)
        self.opened_images = []
        self.last_viewed_images = []
        self.temp_images = {}

        self.init()
        self.temp_dir = tempfile.mkdtemp(prefix="photo_editor-")
        print(self.temp_dir)

        self.open_recent_menu = None

    def init(self):
        self.root.title("Py Photo Editor")
        self.root.iconphoto(True, PhotoImage(file=r"images/photo-icon.png"))
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        # setting tkinter window size
        self.root.geometry("%dx%d" % (width, height))
        self.image_tabs.enable_traversal()
        # self.root.bind("<Escape>,", self._close)
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        # os.mkdir("tmp")

        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as f:
                json.dump({"open_images": [], "last_viewed_images": []}, f)
        else:
            self.load_images_from_config()

    def run(self):
        self.draw_menu()
        self.draw_widgets()
        self.root.mainloop()

    def draw_menu(self):
        menu_bar = Menu(self.root)

        file_menu = Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Открыть...", command=self.open_new_images)

        self.open_recent_menu = Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Недавние файлы", menu=self.open_recent_menu)
        for path in self.last_viewed_images:
            self.open_recent_menu.add_command(label=path, command=lambda x=path: self.add_new_image(x))

        file_menu.add_separator()

        file_menu.add_cascade(label="Отменить последнее действие", command=self.cancel_change)
        file_menu.add_cascade(label="Восстановить", command=self.return_to_original)

        file_menu.add_separator()

        file_menu.add_command(label="Сохранить", command=self.save_current_image)
        file_menu.add_command(label="Сохранить как...", command=self.save_image_as)
        file_menu.add_command(label="Сохранить все", command=self.save_all_changes)
        file_menu.add_separator()

        file_menu.add_command(label="Закрыть изображение", command=self.close_current_image)
        file_menu.add_separator()

        file_menu.add_command(label="Переместить изображение", command=self.move_current_image)
        file_menu.add_command(label="Удалить изображение", command=self.delete_current_image)
        file_menu.add_separator()

        file_menu.add_command(label="Выход", command=self._close)
        menu_bar.add_cascade(label="Файл", menu=file_menu)

        setup_menu = Menu(menu_bar, tearoff=0)
        crop_menu = Menu(setup_menu, tearoff=0)
        # setup_menu.add_command(label="Изменить размер...", command=self.resize_current_image)
        crop_menu.add_command(label="Выделить", command=self.start_crop_selection_of_current_image)
        crop_menu.add_command(label="Сбросить выделение", command=self.cancel_selection)
        crop_menu.add_command(label="Обрезать", command=self.crop_selection_of_current_image)
        setup_menu.add_cascade(label="Обрезать", menu=crop_menu)

        rotate_menu = Menu(setup_menu, tearoff=0)
        rotate_menu.add_command(label="Повернуть на 90 влево", command=lambda: self.rotate_current_image(90))
        rotate_menu.add_command(label="Повернуть на 90 вправо", command=lambda: self.rotate_current_image(-90))
        rotate_menu.add_command(label="Повернуть на 180", command=lambda: self.rotate_current_image(180))
        setup_menu.add_cascade(label="Повернуть", menu=rotate_menu)

        flip_menu = Menu(setup_menu, tearoff=0)
        flip_menu.add_command(label="Отразить по горизонтали", command=lambda: self.flip_current_image(1))
        flip_menu.add_command(label="Отразить по вертикали", command=lambda: self.flip_current_image(0))
        setup_menu.add_cascade(label="Отразить", menu=flip_menu)

        enhance_menu = Menu(setup_menu, tearoff=0)
        enhance_menu.add_command(label="Яркость", command=lambda: self.enhance_current_image("Яркость", "Brightness"))
        enhance_menu.add_command(label="Констраст", command=lambda: self.enhance_current_image("Констраст", "Contrast"))

        enhance_menu.add_command(label="Убрать шум", command=lambda: self.filter_current_image("noisy"))
        enhance_menu.add_command(label="Повысить резкость", command=lambda: self.filter_current_image("sharp"))
        enhance_menu.add_command(label="Размытость", command=lambda: self.filter_current_image("blur"))

        filter_menu = Menu(enhance_menu, tearoff=0)
        filter_menu.add_command(label="Черно-белая пленка", command=lambda: self.filter_current_image("gray"))
        filter_menu.add_command(label="Карандашный эскиз", command=lambda: self.filter_current_image("pencil"))
        filter_menu.add_command(label="Масляная краска", command=lambda: self.filter_current_image("oil_painting"))
        filter_menu.add_command(label="Акварельная краска", command=lambda: self.filter_current_image("water_color"))

        enhance_menu.add_cascade(label="Стилизация", menu=filter_menu)

        menu_bar.add_cascade(label="Изображение", menu=setup_menu)
        menu_bar.add_cascade(label="Настройка", menu=enhance_menu)

        self.root.configure(menu=menu_bar)

    def update_open_recent_menu(self):
        if self.open_recent_menu is None:
            return
        self.open_recent_menu.delete(0, "end")
        for path in self.last_viewed_images:
            self.open_recent_menu.add_command(label=path, command=lambda x=path: self.add_new_image(x))

    # def update_cancel_change(self):
    #     if len(self.temp_images) > 0:


    def draw_widgets(self):
        self.image_tabs.pack(fill="both", expand=1)

    def load_images_from_config(self):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        self.last_viewed_images = config["last_viewed_images"]
        paths = config["opened_images"]
        for path in paths:
            self.add_new_image(path)

    def open_new_images(self):
        image_paths = fd.askopenfilenames(filetypes=(("Images", "*.jpeg; *.jpg; *.png"), ))
        if not image_paths:
            return
        for image_path in image_paths:
            self.add_new_image(image_path)

            if image_path not in self.last_viewed_images:
                self.last_viewed_images.append(image_path)
            else:
                self.last_viewed_images.remove((image_path))
                self.last_viewed_images.append(image_path)
            if len(self.last_viewed_images) > 5:
                del self.last_viewed_images[0]
        self.update_open_recent_menu()

    def add_new_image(self, image_path):
        if not os.path.isfile(image_path):
            if image_path in self.last_viewed_images:
                self.last_viewed_images.remove(image_path)
                self.update_open_recent_menu()
            return
        opened_images = [info.path for info in self.opened_images]
        if image_path in opened_images:
            index = opened_images.index(image_path)
            self.image_tabs.select(index)
            return

        image = cv2.imdecode(np.fromfile(image_path, np.uint8), cv2.IMREAD_UNCHANGED)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_tab = Frame(self.image_tabs)

        image_info = ImageInfo(image, image_path, image_tab)
        self.opened_images.append(image_info)

        # make the canvas expandable
        image_tab.rowconfigure(0, weight=1)
        image_tab.columnconfigure(0, weight=1)

        canvas = Canvas(image_tab, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        canvas.update()  # wait till canvas is created

        image_info.set_canvas(canvas)

        self.image_tabs.add(image_tab, text=image_info.filename())
        self.image_tabs.select(image_tab)

    def current_image(self):
        current_tab = self.image_tabs.select()
        if not current_tab:
            return None
        tab_number = self.image_tabs.index(current_tab)
        return self.opened_images[tab_number]

    def path_temp_image(self, image):
        if image not in self.temp_images:
            return None
        temp_path = os.path.join(self.temp_dir, self.temp_images[image] + "_" + image.filename(no_star=True))
        return temp_path

    def save_current_image(self):
        image = self.current_image()
        if not image:
            return
        if not image.unsaved:
            return
        image.save()
        self.image_tabs.add(image.tab, text=image.filename())

    def save_temp_image(self):
        image = self.current_image()
        if not image:
            return
        if image not in self.temp_images:
            lst = self.temp_images.values()
            name_temp = str(random.randint(111111111, 999999999))
            while True:
                if name_temp not in lst:
                    self.temp_images.update({image: name_temp})
                    break
                else:
                    name_temp = str(random.randint(111111111, 999999999))
        image.save_temp_file(self.path_temp_image(image))

    def save_image_as(self):
        image = self.current_image()
        if not image:
            return
        try:
            image.save_as()
            self.update_image_inside_app(image)

        except ValueError as e:
            mb.showerror("Ошибка сохранения", str(e))

    def cancel_change(self):
        image = self.current_image()
        if not image:
            return
        try:
            image.cancel(self.path_temp_image(image))
            image.unsaved = True
            self.update_image_inside_app(image)
            image.delete_temp_file(self.path_temp_image(image))
        except FileNotFoundError as e:
            mb.showerror("Ошибка операции", str(e))

    def return_to_original(self):
        image = self.current_image()
        if not image:
            return
        if not mb.askyesno("Несохраненные изменения", "Отменить все изменения с момента последнего сохранения?"):
            return
        image_path = image.full_path(no_star=True)
        if self.path_temp_image(image) is not None:
            if os.path.exists(self.path_temp_image(image)):
                image.delete_temp_file(self.path_temp_image(image))
        image.original(image_path)
        image.unsaved = False
        self.update_image_inside_app(image)

    def rotate_current_image(self, degree):
        image = self.current_image()
        if not image:
            return
        self.save_temp_image()
        image.rotate(degree)
        image.unsaved = True
        self.update_image_inside_app(image)

    def flip_current_image(self, mode):
        image = self.current_image()
        if not image:
            return
        self.save_temp_image()
        image.flip(mode)
        image.unsaved = True
        self.update_image_inside_app(image)

    def save_all_changes(self):
        for image_info in self.opened_images:
            if not image_info.unsaved:
                continue
            image_info.save()
            self.image_tabs.tab(image_info.tab, text=image_info.filename())

    def close_current_image(self):
        image = self.current_image()
        if not image:
            return
        if image.unsaved:
            if not mb.askyesno("Несохраненные изменения", "Закрыть без сохранения?"):
                return
        image.close()
        if self.path_temp_image(image) is not None:
            if os.path.exists(self.path_temp_image(image)):
                image.delete_temp_file(self.path_temp_image(image))
        self.image_tabs.forget(image.tab)
        self.opened_images.remove(image)

    def delete_current_image(self):
        image = self.current_image()
        if not image:
            return

        if not mb.askokcancel("Удаление изображения", "Вы уверены, что хотите удалить изображение?"):
            return
        if self.path_temp_image(image) is not None:
            if os.path.exists(self.path_temp_image(image)):
                image.delete_temp_file(self.path_temp_image(image))
        image.delete()
        self.image_tabs.forget(image.tab)
        self.opened_images.remove(image)

    def move_current_image(self):
        image = self.current_image()
        if not image:
            return
        image.move()
        self.update_image_inside_app(image)

    def update_image_inside_app(self, image_info):
        image_info.update_image_on_canvas()
        self.image_tabs.tab(image_info.tab, text=image_info.filename())

    def start_crop_selection_of_current_image(self):
        image = self.current_image()
        if not image:
            return
        image.start_crop_sel()

    def crop_selection_of_current_image(self):
        image = self.current_image()
        if not image:
            return
        try:
            self.save_temp_image()
            image.crop_selected_area()
            image.unsaved = True
            self.update_image_inside_app(image)
        except ValueError as e:
            mb.showerror("Ошибка операции", str(e))

    def cancel_selection(self):
        image = self.current_image()
        if not image:
            return
        try:
            image.cancel_sel()
        except ValueError as e:
            mb.showerror("Ошибка операции", str(e))

    def enhance_current_image(self, name, enhance):
        image = self.current_image()
        if not image:
            return
        EnhanceSliderWindow(self.root, name, enhance, image, self.update_image_inside_app,
                            self.path_temp_image(image))

    def filter_current_image(self, mode):
        image = self.current_image()
        if not image:
            return
        self.save_temp_image()
        image.filter(mode)
        image.unsaved = True
        self.update_image_inside_app(image)

    def save_images_to_config(self):
        paths = [info.full_path(no_star=True) for info in self.opened_images]
        images = {"opened_images": paths, "last_viewed_images": self.last_viewed_images}
        with open(CONFIG_FILE, "w") as f:
            json.dump(images, f, indent=4)

    def unsaved_images(self):
        for info in self.opened_images:
            if info.unsaved:
                return True
        return False

    def _close(self, event=None):
        if self.unsaved_images():
            if not mb.askyesno("Несохраненные изменения", "Есть несохраненные изменения. Продолжить выход?"):
                return
        self.save_images_to_config()
        # self.temp_dir.cleanup()
        shutil.rmtree(self.temp_dir)
        # shutil.rmtree("tmp")
        self.root.quit()


if __name__ == "__main__":
    PyPhotoEditor().run()
