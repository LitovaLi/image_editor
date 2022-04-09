from image_edit import ImageEdit
import os
from tkinter import filedialog as fd
from PIL import Image
import shutil


class ImageInfo(ImageEdit):
    def __init__(self, image, path, tab):
        super().__init__(image)

        self.path = path
        self.tab = tab

    @property
    def unsaved(self) -> bool:
        return self.path[-1] == "*"

    @unsaved.setter
    def unsaved(self, value: bool):
        if value and not self.unsaved:
            self.path += "*"
        elif not value and self.unsaved:
            self.path = self.path[:-1]

    def filename(self, no_star=False):
        name = os.path.split(self.path)[1]
        return name[:-1] if no_star and name[-1] == "*" else name

    def file_extension(self, no_star=False):
        ext = os.path.splitext(self.path)[1]
        return ext[:-1] if no_star and ext[-1] == "*" else ext

    def directory(self, no_star=False):
        dirname = os.path.split(self.path)[1]
        return dirname[:-1] if no_star and dirname[-1] == "*" else dirname

    def full_path(self, no_star=False):
        return self.path[:-1] if no_star and self.path[-1] == "*" else self.path

    def save(self):
        if not self.unsaved:
            return
        self.unsaved = False
        Image.fromarray(self.image).save(self.path)

    def save_temp_file(self, temp_path):
        Image.fromarray(self.image).save(temp_path)

    def delete_temp_file(self, temp_path):
        os.remove(temp_path)

    def save_as(self):
        old_ext = self.file_extension(no_star=True)
        new_path = fd.asksaveasfilename(
            initialdir=self.full_path(no_star=True),
            filetypes=[("Images", "*.jpeg; *.jpg; *.png"), ]
        )
        if not new_path:
            return
        new_path, new_ext = os.path.splitext(new_path)
        if not new_ext:
            new_ext = old_ext
        elif new_ext != old_ext:
            raise ValueError(f"Выбрано неверное расширение файла: '{new_ext}'. Старое расширение файла: '{old_ext}'")
        Image.fromarray(self.image).save(new_path + new_ext)
        Image.fromarray(self.image).close()

        self.path = new_path + new_ext
        self.unsaved = False
        self.update_image_on_canvas()

    def close(self):
        Image.fromarray(self.image).close()
        Image.fromarray(self.original_image).close()

    def delete(self):
        self.close()
        os.remove(self.full_path(no_star=True))

    def move(self):
        new_dir = fd.askdirectory(initialdir=self.directory(no_star=True))
        if not new_dir:
            return
        new_path = os.path.join(new_dir, self.filename(no_star=True))
        Image.fromarray(self.image).close()
        shutil.move(self.full_path(no_star=True), new_path)

        self.path = new_path
        self.unsaved = False
        self.update_image_on_canvas()
