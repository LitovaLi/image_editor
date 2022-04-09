from tkinter import *
import cv2
import numpy as np


class EnhanceSliderWindow(Toplevel):
    def __init__(self, root, name, enhance, image_info, update_method, temp_path):
        super().__init__(root)

        self.name = name
        self.image_info = image_info
        self.original_image = image_info.image
        self.enhance = enhance
        self.update_method = update_method
        self.temp_path = temp_path

        self.init()

        self.factor_alpha = DoubleVar(value=1.0)
        self.scroll_alpha = Scale(
            self, label=self.name,
            from_=0.1, to=2.0, resolution=0.1, variable=self.factor_alpha,
            orient="horizontal",
            command=self.value_changed
        )

        self.apply = Button(self, text="Применить", command=self.apply)
        self.cancel = Button(self, text="Отменить", command=self.cancel)
        self.draw_widgets()

    def init(self):
        self.title(self.name)
        self.grab_focus()
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    def grab_focus(self):
        self.grab_set()
        self.focus_set()

    def draw_widgets(self):
        self.scroll_alpha.pack(fill="x", expand=1, pady=5, padx=5)
        self.apply.pack(side="left", expand=1, pady=5, padx=5)
        self.cancel.pack(side="left", expand=1, pady=5, padx=5)

    def value_changed(self, _):
        if self.enhance == "Contrast":
            value = 1.0 / self.factor_alpha.get()
            table = np.array([((i / 255.0) ** value) * 255
                              for i in np.arange(0, 256)]).astype("uint8")
            image = cv2.LUT(self.original_image, table)
            self.image_info.set_image(image)

        if self.enhance == "Brightness":
            image = cv2.convertScaleAbs(self.original_image, alpha=self.factor_alpha.get(), beta=0)
            self.image_info.set_image(image)

        self.image_info.update_image_on_canvas()

    def apply(self):
        self.image_info.unsaved = True
        self.update_method(self.image_info)
        self.save_temp()
        self.close()

    def save_temp(self):
        self.image_info.set_image(self.original_image)
        self.image_info.save_temp_file(self.temp_path)

    def cancel(self):
        self.image_info.set_image(self.original_image)
        self.image_info.update_image_on_canvas()

        self.update_method(self.image_info)
        self.close()

    def close(self):
        self.destroy()
