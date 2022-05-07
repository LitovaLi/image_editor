from PIL import Image, ImageTk
import cv2
import numpy as np
from coordinates import Rect
import os
from mask import Paint



class ImageEdit:
    def __init__(self, image):
        self.original_image = image
        self.image = image.copy()

        self.canvas = None
        self.zoom_container = None
        self.image_container = None

        self.imscale = 1.0
        self.zoom_delta = 1.3

        self.crop_selection = None
        self.sel_change_side = ""
        self.sel_rect = None
        self.sel_mov_x = 0
        self.sel_mov_y = 0

    @property
    def image_tk(self):
        image_tk = Image.fromarray(self.image)
        return ImageTk.PhotoImage(image_tk)

    def image_tk_fun(self):
         return Image.fromarray(self.image)

    def set_canvas(self, canvas):
        self.canvas = canvas
        self._bind_zoom()
        self.zoom_container = self.canvas.create_rectangle(0, 0, self.image_tk.width(), self.image_tk.height(), width=0)
        self.canvas.image = self.image_tk
        self._show_zoomed_image()

    def update_image_on_canvas(self):
        if self.canvas is None:
            raise RuntimeError("Картинка не установлена")
        self._show_zoomed_image()

    def cancel(self, temp_path):
        if temp_path is None:
            raise FileNotFoundError("Изменений нет")
        if os.path.exists(temp_path):
            image = cv2.imdecode(np.fromfile(temp_path, np.uint8), cv2.IMREAD_UNCHANGED)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self.set_image(image)
            self.set_canvas(self.canvas)
        else:
            raise FileNotFoundError("Изменений нет")

    def original(self, image_path):
        if os.path.exists(image_path):
            image = cv2.imdecode(np.fromfile(image_path, np.uint8), cv2.IMREAD_UNCHANGED)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            self.set_image(image)
            self.set_canvas(self.canvas)

    def rotate(self, degree):
        if degree == 90:
            self.image = cv2.rotate(self.image, cv2.ROTATE_90_CLOCKWISE)
        if degree == -90:
            self.image = cv2.rotate(self.image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        if degree == 180:
            self.image = cv2.rotate(self.image, cv2.ROTATE_180)
        self.set_canvas(self.canvas)
        self._reset_zoom()

    def flip(self, mode):
        self.image = cv2.flip(self.image, mode)

    def filter(self, mode):
        if mode == "pencil":
            img_gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            img_blur = cv2.GaussianBlur(img_gray, (21, 21), 0, 0)
            img_blend = cv2.divide(img_gray, img_blur, scale=256)
            self.image = cv2.cvtColor(img_blend, cv2.COLOR_GRAY2BGR)

        if mode == "oil_painting":
            self.image = cv2.xphoto.oilPainting(self.image, 7, 1)

        if mode == "water_color":
            res = cv2.stylization(self.image, sigma_s=60, sigma_r=0.6)
            self.image = res

        if mode == "noisy":
            self.image = cv2.fastNlMeansDenoisingColored(self.image, None, 5, 5, 7, 21)

        if mode == "sharp":
            kernel = np.array([[0, -1, 0],
                               [-1, 5, -1],
                               [0, -1, 0]])
            sharpened = cv2.filter2D(self.image, -1, kernel)  # applying the sharpening kernel to the input image & displaying it.
            self.image = sharpened

        if mode == "blur":
            gaus_blur = cv2.GaussianBlur(self.image, (5, 5), 0)
            self.image = gaus_blur

    def paint_mask(self, temp_dir, id_temp):
        Paint(temp_dir, self.image, id_temp)

    def inpaint(self, temp_dir, id_temp):
        mask = cv2.imread(os.path.join(temp_dir, id_temp + "_mask.png"), 0)
        # image = cv2.inpaint(self.image, mask, 10, cv2.INPAINT_TELEA)
        image = cv2.inpaint(self.image, mask, 5, cv2.INPAINT_NS)
        self.image = image

    def start_crop_sel(self):
        self._unbind_zoom()
        if self.crop_selection is not None:
            self.canvas.delete(self.sel_rect)
            self.sel_rect = None

        bbox = self.canvas.bbox(self.image_container)
        self.crop_selection = Rect(*bbox, side_offset=5)

        self.sel_rect = self.canvas.create_rectangle(
            *self.crop_selection.coordinates,
            dash=(10, 10), outline="blue",
            width=2
        )

        self._bind_crop()

    def start_paint(self):
        self._unbind_zoom()

        bbox = self.canvas.bbox(self.image_container)
        self.crop_selection = Rect(*bbox, side_offset=5)

        self.sel_rect = self.canvas.create_rectangle(
            *self.crop_selection.coordinates,
            dash=(10, 10), outline="blue",
            width=2
        )

        self._bind_crop()

    def _bind_crop(self):
        self.canvas.bind("<Motion>", self._change_crop_cursor)
        self.canvas.bind("<B1-Motion>", self._move_crop_side)
        self.canvas.bind("<ButtonPress-1>", self._start_crop_area_movement)
        self.canvas.bind("<Double-Button-1>", self._set_crop_area_on_full_image)

    def _unbind_crop(self):
        self.canvas.unbind("<Motion>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<Double-Button-1>")
        self.canvas["cursor"] = ""

    def _change_crop_cursor(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self.crop_selection.top_left.point_inside(x, y):
            self.canvas["cursor"] = "top_left_corner"
            self.sel_change_side = "top_left"
        elif self.crop_selection.top_right.point_inside(x, y):
            self.canvas["cursor"] = "top_right_corner"
            self.sel_change_side = "top_right"
        elif self.crop_selection.bottom_left.point_inside(x, y):
            self.canvas["cursor"] = "bottom_left_corner"
            self.sel_change_side = "bottom_left"
        elif self.crop_selection.bottom_right.point_inside(x, y):
            self.canvas["cursor"] = "bottom_right_corner"
            self.sel_change_side = "bottom_right"
        elif self.crop_selection.top.point_inside(x, y):
            self.canvas["cursor"] = "top_side"
            self.sel_change_side = "top"
        elif self.crop_selection.left.point_inside(x, y):
            self.canvas["cursor"] = "left_side"
            self.sel_change_side = "left"
        elif self.crop_selection.bottom.point_inside(x, y):
            self.canvas["cursor"] = "bottom_side"
            self.sel_change_side = "bottom"
        elif self.crop_selection.right.point_inside(x, y):
            self.canvas["cursor"] = "right_side"
            self.sel_change_side = "right"
        elif self.crop_selection.center(offset=100).point_inside(x, y):
            self.canvas["cursor"] = "sizing"
            self.sel_change_side = "center"
        else:
            self.canvas["cursor"] = ""
            self.sel_change_side = ""

    def _move_crop_side(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        bbox = self.canvas.bbox(self.image_container)
        image = Rect(*bbox)

        if self.sel_change_side == "top_left":
            x = max(x, image.x0)
            y = max(y, image.y0)
            if self.crop_selection.width < 20:
                x = min(self.crop_selection.x0, x)
            if self.crop_selection.height < 20:
                y = min(self.crop_selection.y0, y)
            self.crop_selection.change(x0=x, y0=y)

        elif self.sel_change_side == "top_right":
            x = min(x, image.x1)
            y = max(y, image.y0)
            if self.crop_selection.width < 20:
                x = max(self.crop_selection.x1, x)
            if self.crop_selection.height < 20:
                y = min(self.crop_selection.y0, y)
            self.crop_selection.change(x1=x, y0=y)

        elif self.sel_change_side == "bottom_left":
            x = max(x, image.x0)
            y = min(y, image.y1)
            if self.crop_selection.width < 20:
                x = min(self.crop_selection.x0, x)
            if self.crop_selection.height < 20:
                y = max(self.crop_selection.y1, y)
            self.crop_selection.change(x0=x, y1=y)

        elif self.sel_change_side == "bottom_right":
            x = min(x, image.x1)
            y = min(y, image.y1)
            if self.crop_selection.width < 20:
                x = max(self.crop_selection.x1, x)
            if self.crop_selection.height < 20:
                y = max(self.crop_selection.y1, y)
            self.crop_selection.change(x1=x, y1=y)

        elif self.sel_change_side == "top":
            y = max(y, image.y0)
            if self.crop_selection.height < 20:
                y = min(self.crop_selection.y0, y)
            self.crop_selection.change(y0=y)
        elif self.sel_change_side == "left":
            x = max(x, image.x0)
            if self.crop_selection.width < 20:
                x = min(self.crop_selection.x0, x)
            self.crop_selection.change(x0=x)
        elif self.sel_change_side == "bottom":
            y = min(y, image.y1)
            if self.crop_selection.height < 20:
                y = max(self.crop_selection.y1, y)
            self.crop_selection.change(y1=y)
        elif self.sel_change_side == "right":
            x = min(x, image.x1)
            if self.crop_selection.width < 20:
                x = max(self.crop_selection.x1, x)
            self.crop_selection.change(x1=x)

        elif self.sel_change_side == "center":
            dx = x - self.sel_mov_x
            dy = y - self.sel_mov_y
            self.sel_mov_x = x
            self.sel_mov_y = y

            if self.crop_selection == image:
                return

            w = self.crop_selection.width
            h = self.crop_selection.height

            x0 = self.crop_selection.x0 + dx
            x1 = self.crop_selection.x1 + dx
            if x0 < image.x0:
                x0 = image.x0
                x1 = x0 + w
            if x1 > image.x1:
                x1 = image.x1
                x0 = x1 - w

            y0 = self.crop_selection.y0 + dy
            y1 = self.crop_selection.y1 + dy
            if y0 < image.y0:
                y0 = image.y0
                y1 = y0 + h
            if y1 > image.y1:
                y1 = image.y1
                y0 = y1 - h

            self.crop_selection.change(x0=x0, y0=y0, x1=x1, y1=y1)

        self.canvas.coords(self.sel_rect, *self.crop_selection.coordinates)

    def _set_crop_area_on_full_image(self, event):
        bbox = self.canvas.bbox(self.image_container)
        self.crop_selection = Rect(*bbox, side_offset=5)
        self.canvas.coords(self.sel_rect, *bbox)

    def _start_crop_area_movement(self, event):
        if self.sel_change_side == "center":
            self.sel_mov_x = self.canvas.canvasx(event.x)
            self.sel_mov_y = self.canvas.canvasy(event.y)

    def crop_selected_area(self):
        if self.sel_rect is None:
            raise ValueError("Область не выделена")

        self._unbind_crop()
        bbox = self.canvas.bbox(self.image_container)
        image = Rect(*bbox)

        dx0 = (self.crop_selection.x0 - image.x0) / image.width
        dx1 = (image.width - (image.x1 - self.crop_selection.x1)) / image.width
        dy0 = (self.crop_selection.y0 - image.y0) / image.height
        dy1 = (image.height - (image.y1 - self.crop_selection.y1)) / image.height

        self.canvas.delete(self.sel_rect)
        self.sel_rect = None

        x0 = int(dx0 * self.image_tk.width())
        y0 = int(dy0 * self.image_tk.height())
        x1 = int(dx1 * self.image_tk.width())
        y1 = int(dy1 * self.image_tk.height())

        if x0 == 0 and y0 == 0 and x1 == image.width and y1 == image.height:
            self.crop_selection = None
            self._bind_zoom()
            return
        self.image = self.image[y0:y1, x0:x1]
        self._reset_zoom()
        self.crop_selection = None
        self._bind_zoom()

    def cancel_sel(self):
        if self.sel_rect is None:
            raise ValueError("Область не выделена")

        self._unbind_crop()
        self.canvas["cursor"] = ""

        self._bind_zoom()
        self.canvas.delete(self.sel_rect)
        self.sel_rect = None
        self.crop_selection = None

    def set_image(self, image):
        self.image = image

    def _bind_zoom(self):
        self.canvas.bind("<ButtonPress-1>", self._move_from)
        self.canvas.bind("<B1-Motion>", self._move_to)
        self.canvas.bind("<MouseWheel>", self._zoom_with_wheel)  # Windows and MacOS
        self.canvas.bind("<Button-4>", self._zoom_with_wheel)  # Linux
        self.canvas.bind("<Button-5>", self._zoom_with_wheel)  # linux

    def _unbind_zoom(self):
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<B-1>")
        self.canvas.unbind("<MouseWheel>")  # Windows and MacOS
        self.canvas.unbind("<Button-4>")  # Linux
        self.canvas.unbind("<Button-5>")  # linux

    def _reset_zoom(self):
        self.imscale = 1.0
        cx, cy = self.canvas.canvasx(0), self.canvas.canvasy(0)
        self.canvas.delete(self.zoom_container)
        self.zoom_container = self.canvas.create_rectangle(cx, cy, self.image_tk.width() + cx, self.image_tk.height() + cy, width=0)

    def _move_from(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def _move_to(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self._show_zoomed_image()

    def _zoom_with_wheel(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        bbox = self.canvas.bbox(self.zoom_container)
        image_area = Rect(*bbox)

        if not (image_area.x0 < x < image_area.x1 and image_area.y0 < y < image_area.y1):
            return

        scale = 1.0
        # event.num - Linux, event.delta - Windows and MacOS
        if event.num == 5 or event.delta == -120:
            # scroll down
            image_tk = self.image_tk_fun()
            i = min(image_tk.width, image_tk.height)
            if int(i * self.imscale) < 30:
                return
            self.imscale /= self.zoom_delta
            scale /= self.zoom_delta

        if event.num == 4 or event.delta == 120:
            # scroll up
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
            # visible area is greater that scale
            if i < self.imscale:
                return
            self.imscale *= self.zoom_delta
            scale *= self.zoom_delta

        # rescale all canvas objects
        self.canvas.scale("all", x, y, scale, scale)
        self._show_zoomed_image()

    def _show_zoomed_image(self, event=None):
        bbox = self.canvas.bbox(self.zoom_container)
        rect = Rect(*bbox)
        # Remove 1 pixel at the sides of bbox
        rect.x0 += 1
        rect.y0 += 1
        rect.x1 -= 1
        rect.y1 -= 1

        # get visible area
        visible = Rect(
            self.canvas.canvasx(0), self.canvas.canvasy(0),
            self.canvas.canvasx(self.canvas.winfo_width()),
            self.canvas.canvasy(self.canvas.winfo_height())
        )

        # get scroll region box
        scroll = Rect(
            min(rect.x0, visible.x0), min(rect.y0, visible.y0),
            max(rect.x1, visible.x1), max(rect.y1, visible.y1)
        )

        # whole image in the visible area
        if scroll.x0 == visible.x0 and scroll.x1 == visible.x1:
            scroll.x0 = rect.x0
            scroll.x1 = rect.x1
        if scroll.y0 == visible.y0 and scroll.y1 == visible.y1:
            scroll.y0 = rect.y0
            scroll.y1 = rect.y1

        self.canvas.configure(scrollregion=scroll.coordinates)

        # get coordinates of the image tile
        tile = Rect(
            max(scroll.x0 - rect.x0, 0), max(scroll.y0 - rect.y0, 0),
            min(scroll.x1, rect.x1) - rect.x0,
            min(scroll.y1, rect.y1) - rect.y0
        )

        # show image if it is in the visible area
        image_tk = self.image_tk_fun()

        if tile.width > 0 and tile.height > 0:
            x = min(int(tile.x1 / self.imscale), image_tk.width)
            y = min(int(tile.y1 / self.imscale), image_tk.height)

            image = image_tk.crop([int(tile.x0 / self.imscale), int(tile.y0 / self.imscale), x, y])
            imagetk = ImageTk.PhotoImage(image.resize([int(tile.width), int(tile.height)]))

            if self.image_container is not None:
                self.canvas.delete(self.image_container)

            self.image_container = self.canvas.create_image(
                max(scroll.x0, rect.x0), max(scroll.y0, rect.y0),
                anchor="nw", image=imagetk
            )

            # set image into background
            self.canvas.lower(self.image_container)
            # keep extra reference to prevent garbage-collection
            self.canvas.imagetk = imagetk
