import os
import tkinter as tk
import tkinter.colorchooser as colorchooser
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import random


class ImagePainter:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Painter")

        self.original_image = None
        self.image = None
        self.display_image = None
        self._processed = None
        self._contour_info = ""

        self.load_button = tk.Button(root, text="Load Image", command=self.load_image)
        self.load_button.pack()

        resize_frame = tk.Frame(root)
        resize_frame.pack()

        tk.Label(resize_frame, text="Width:").grid(row=0, column=0)
        self.width_entry = tk.Entry(resize_frame)
        self.width_entry.grid(row=0, column=1)

        tk.Label(resize_frame, text="Height:").grid(row=1, column=0)
        self.height_entry = tk.Entry(resize_frame)
        self.height_entry.grid(row=1, column=1)

        tk.Button(resize_frame, text="Resize", command=self.resize_image).grid(row=2, column=0)
        tk.Button(resize_frame, text="Save", command=self.save_image).grid(row=2, column=1)
        tk.Button(resize_frame, text="Save View", command=self.save_view).grid(row=2, column=2)

        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack()

        self.h_scroll = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll = tk.Scrollbar(root, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)

        self.dragging = False
        self.zoom_level = 1.0
        self._contour_polys = None
        self._component_pixels = None
        self._undo_stack = []
        self._redo_stack = []
        self._max_undo = 50

        view_frame = tk.Frame(root)
        view_frame.pack()
        tk.Label(view_frame, text="View Mode:").pack(side=tk.LEFT)
        self.view_mode = tk.StringVar(value="BGR")
        self.view_dropdown = tk.OptionMenu(
            view_frame, self.view_mode, "BGR", "Grayscale", "Binary", "Contours", "Flood Fill",
            command=self.on_view_change
        )
        self.view_dropdown.pack(side=tk.LEFT)

        zoom_frame = tk.Frame(root)
        zoom_frame.pack()
        tk.Button(zoom_frame, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT)
        tk.Button(zoom_frame, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT)
        tk.Button(zoom_frame, text="Reset Zoom", command=self.zoom_reset).pack(side=tk.LEFT)

        undo_frame = tk.Frame(root)
        undo_frame.pack()
        tk.Button(undo_frame, text="Undo", command=self.undo).pack(side=tk.LEFT)
        tk.Button(undo_frame, text="Redo", command=self.redo).pack(side=tk.LEFT)

        mouse_frame = tk.Frame(root)
        mouse_frame.pack()
        tk.Label(mouse_frame, text="Mouse:").pack(side=tk.LEFT)
        self.mouse_mode = tk.StringVar(value="Drag")
        self.mouse_dropdown = tk.OptionMenu(
            mouse_frame, self.mouse_mode, "Drag", "Random Color", "Paint Color", "Pick Color"
        )
        self.mouse_dropdown.pack(side=tk.LEFT)

        color_frame = tk.Frame(root)
        color_frame.pack()
        self.selected_color = (255, 0, 0, 255)
        self.color_preview = tk.Label(color_frame, width=4, bg="red", relief=tk.SUNKEN)
        self.color_preview.pack(side=tk.LEFT, padx=2)
        tk.Button(color_frame, text="Pick", command=self.pick_color).pack(side=tk.LEFT)
        tk.Label(color_frame, text="R:").pack(side=tk.LEFT, padx=(8, 0))
        self.r_entry = tk.Entry(color_frame, width=4)
        self.r_entry.insert(0, "255")
        self.r_entry.pack(side=tk.LEFT)
        tk.Label(color_frame, text="G:").pack(side=tk.LEFT)
        self.g_entry = tk.Entry(color_frame, width=4)
        self.g_entry.insert(0, "0")
        self.g_entry.pack(side=tk.LEFT)
        tk.Label(color_frame, text="B:").pack(side=tk.LEFT)
        self.b_entry = tk.Entry(color_frame, width=4)
        self.b_entry.insert(0, "0")
        self.b_entry.pack(side=tk.LEFT)
        tk.Label(color_frame, text="A:").pack(side=tk.LEFT)
        self.a_entry = tk.Entry(color_frame, width=4)
        self.a_entry.insert(0, "255")
        self.a_entry.pack(side=tk.LEFT)
        self.r_entry.bind("<KeyRelease>", self._update_color_from_entries)
        self.g_entry.bind("<KeyRelease>", self._update_color_from_entries)
        self.b_entry.bind("<KeyRelease>", self._update_color_from_entries)
        self.a_entry.bind("<KeyRelease>", self._update_color_from_entries)

        self.info_label = tk.Label(root, text="No image loaded", justify=tk.LEFT)
        self.info_label.pack()

        self.contour_info_label = tk.Label(root, text="", justify=tk.LEFT)
        self.contour_info_label.pack()

        self._try_load_default()

    def _try_load_default(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_path = os.path.join(script_dir, "test.png")
        if os.path.isfile(default_path):
            self.original_image = Image.open(default_path).convert('RGBA')
            self.image = self.original_image.copy()
            self.zoom_level = 1.0
            self._compute_view()
            self.update_display()
            self.update_info()

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if file_path:
            self.original_image = Image.open(file_path).convert('RGBA')
            self.image = self.original_image.copy()
            self.zoom_level = 1.0
            self._compute_view()
            self.update_display()
            self.update_info()

    def _compute_view(self):
        self._save_snapshot()
        self._contour_polys = None
        self._component_pixels = None

        if not self.image:
            self._processed = None
            self._contour_info = ""
            return

        composite = self.image.copy()
        view = self.view_mode.get()

        if view == "Grayscale":
            composite = composite.convert('L')
            self._contour_info = ""
        elif view == "Binary":
            composite = composite.convert('L').point(lambda p: 0 if p < 127 else 255)
            self._contour_info = ""
        elif view == "Contours":
            binary = composite.convert('L').point(lambda p: 0 if p < 127 else 255)
            binary_np = np.array(binary)
            contours, _ = cv2.findContours(binary_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            color_img = np.zeros((binary_np.shape[0], binary_np.shape[1], 4), dtype=np.uint8)
            color_img[:, :, 3] = 255
            for contour in contours:
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)
                cv2.fillPoly(color_img, [contour], color)
            cv2.drawContours(color_img, contours, -1, (0, 0, 0, 255), 1)
            composite = Image.fromarray(color_img, 'RGBA')
            num_contours = len(contours)
            total_area = sum(cv2.contourArea(c) for c in contours)
            self._contour_polys = contours
            self._contour_info = f"Contours: {num_contours}, Total area: {total_area:.0f}px²"
        elif view == "Flood Fill":
            binary = composite.convert('L').point(lambda p: 0 if p < 127 else 255)
            binary_np = np.array(binary)
            h, w = binary_np.shape
            visited = np.zeros_like(binary_np, dtype=bool)
            color_img = np.zeros((h, w, 4), dtype=np.uint8)
            color_img[:, :, 3] = 255
            components = []

            for y in range(h):
                for x in range(w):
                    if binary_np[y, x] > 127 and not visited[y, x]:
                        stack = [(x, y)]
                        pixels = []
                        while stack:
                            cx, cy = stack.pop()
                            if cx < 0 or cx >= w or cy < 0 or cy >= h:
                                continue
                            if visited[cy, cx] or binary_np[cy, cx] <= 127:
                                continue
                            visited[cy, cx] = True
                            pixels.append((cx, cy))
                            stack.extend([(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)])
                        if len(pixels) > 10:
                            components.append(pixels)

            for component in components:
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)
                for px, py in component:
                    color_img[py, px] = color

            composite = Image.fromarray(color_img, 'RGBA')
            num_contours = len(components)
            total_area = sum(len(c) for c in components)
            self._component_pixels = components
            self._contour_info = f"Flood fill: {num_contours}, Total area: {total_area:.0f}px²"
        else:
            self._contour_info = ""

        self._processed = composite

    def update_display(self):
        self.canvas.delete("all")
        if not self.image:
            self.canvas.config(scrollregion=(0, 0, 800, 600))
            return

        composite = self._processed.copy() if self._processed is not None else self.image.copy()
        self.contour_info_label.config(text=self._contour_info)

        if self.zoom_level != 1.0:
            new_w = int(composite.width * self.zoom_level)
            new_h = int(composite.height * self.zoom_level)
            composite = composite.resize((new_w, new_h), Image.LANCZOS)

        self.display_image = ImageTk.PhotoImage(composite)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.display_image)
        self.canvas.config(scrollregion=(0, 0, composite.width, composite.height))

    def _get_image_coords(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        return int(canvas_x / self.zoom_level), int(canvas_y / self.zoom_level)

    def _on_click(self, event):
        mode = self.mouse_mode.get()
        if mode == "Drag":
            if not self.image:
                return
            self.canvas.scan_mark(event.x, event.y)
            self.dragging = True
        elif mode == "Random Color":
            self._click_contour(event, random_color=True)
        elif mode == "Paint Color":
            self._click_contour(event, random_color=False)
        elif mode == "Pick Color":
            self._click_pick_color(event)

    def _on_drag(self, event):
        if self.mouse_mode.get() != "Drag" or not self.dragging:
            return
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _click_contour(self, event, random_color):
        if not self.image or self._processed is None:
            return
        self._save_snapshot()
        img_x, img_y = self._get_image_coords(event)
        view = self.view_mode.get()

        if view == "Contours" and self._contour_polys is not None:
            np_img = np.array(self._processed)
            for contour in self._contour_polys:
                if cv2.pointPolygonTest(contour, (img_x, img_y), False) >= 0:
                    if random_color:
                        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)
                    else:
                        color = self.selected_color
                    cv2.fillPoly(np_img, [contour], color)
                    cv2.drawContours(np_img, [contour], -1, (0, 0, 0, 255), 1)
                    self._processed = Image.fromarray(np_img, 'RGBA')
                    self.update_display()
                    return

        elif view == "Flood Fill" and self._component_pixels is not None:
            np_img = np.array(self._processed)
            for pixels in self._component_pixels:
                for px, py in pixels:
                    if px == img_x and py == img_y:
                        if random_color:
                            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 255)
                        else:
                            color = self.selected_color
                        for cx, cy in pixels:
                            np_img[cy, cx] = color
                        self._processed = Image.fromarray(np_img, 'RGBA')
                        self.update_display()
                        return

    def _click_pick_color(self, event):
        if self._processed is None:
            return
        img_x, img_y = self._get_image_coords(event)
        if img_x < 0 or img_x >= self._processed.width or img_y < 0 or img_y >= self._processed.height:
            return
        pixel = self._processed.getpixel((img_x, img_y))
        if isinstance(pixel, int):
            r = g = b = pixel
            a = 255
        else:
            r, g, b, a = pixel[:4] if len(pixel) >= 4 else (*pixel[:3], 255)
        self.selected_color = (r, g, b, a)
        self.r_entry.delete(0, tk.END)
        self.r_entry.insert(0, str(r))
        self.g_entry.delete(0, tk.END)
        self.g_entry.insert(0, str(g))
        self.b_entry.delete(0, tk.END)
        self.b_entry.insert(0, str(b))
        self.a_entry.delete(0, tk.END)
        self.a_entry.insert(0, str(a))
        self._update_preview()

    def _current_snapshot(self):
        return (
            self._processed.copy() if self._processed is not None else None,
            self._contour_info,
            [c.copy() for c in self._contour_polys] if self._contour_polys is not None else None,
            [list(p) for p in self._component_pixels] if self._component_pixels is not None else None,
        )

    def _restore_snapshot(self, snapshot):
        processed, contour_info, contour_polys, component_pixels = snapshot
        self._processed = processed.copy() if processed is not None else None
        self._contour_info = contour_info
        self._contour_polys = contour_polys
        self._component_pixels = component_pixels

    def _save_snapshot(self):
        self._undo_stack.append(self._current_snapshot())
        if len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self):
        if not self._undo_stack:
            return
        self._redo_stack.append(self._current_snapshot())
        self._restore_snapshot(self._undo_stack.pop())
        self.update_display()
        self.update_info()

    def redo(self):
        if not self._redo_stack:
            return
        self._undo_stack.append(self._current_snapshot())
        self._restore_snapshot(self._redo_stack.pop())
        self.update_display()
        self.update_info()

    def zoom_in(self):
        self.zoom_level *= 1.25
        self.update_display()

    def zoom_out(self):
        self.zoom_level = max(self.zoom_level / 1.25, 0.1)
        self.update_display()

    def zoom_reset(self):
        self.zoom_level = 1.0
        self.update_display()

    def on_view_change(self, value):
        self._compute_view()
        self.update_display()

    def resize_image(self):
        if self.original_image:
            try:
                width = int(self.width_entry.get())
                height = int(self.height_entry.get())
                self.image = self.original_image.resize((width, height), Image.LANCZOS)
                self._compute_view()
                self.update_display()
                self.update_info()
            except ValueError:
                pass

    def save_image(self):
        if not self.image:
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension='.png',
            filetypes=[('PNG', '*.png'), ('JPEG', '*.jpg;*.jpeg'), ('BMP', '*.bmp')]
        )
        if file_path:
            image = self.image.copy()
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                image = image.convert('RGB')
            image.save(file_path)

    def save_view(self):
        if self._processed is None:
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension='.png',
            filetypes=[('PNG', '*.png'), ('JPEG', '*.jpg;*.jpeg'), ('BMP', '*.bmp')]
        )
        if file_path:
            image = self._processed.copy()
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                image = image.convert('RGB')
            image.save(file_path)

    def update_info(self):
        if self.image:
            size = (self.image.width, self.image.height)
            self.info_label.config(text=f"Image: {size[0]}x{size[1]}px")
        else:
            self.info_label.config(text="No image loaded")

    def pick_color(self):
        r, g, b = self.selected_color[:3]
        result = colorchooser.askcolor(color=(r, g, b), title="Choose Color")
        if result and result[0]:
            r, g, b = (int(c) for c in result[0])
            a = self.selected_color[3]
            self.selected_color = (r, g, b, a)
            self.r_entry.delete(0, tk.END)
            self.r_entry.insert(0, str(r))
            self.g_entry.delete(0, tk.END)
            self.g_entry.insert(0, str(g))
            self.b_entry.delete(0, tk.END)
            self.b_entry.insert(0, str(b))
            self._update_preview()

    def _update_color_from_entries(self, event=None):
        try:
            r = min(255, max(0, int(self.r_entry.get() or 0)))
            g = min(255, max(0, int(self.g_entry.get() or 0)))
            b = min(255, max(0, int(self.b_entry.get() or 0)))
            a = min(255, max(0, int(self.a_entry.get() or 0)))
            self.selected_color = (r, g, b, a)
            self._update_preview()
        except ValueError:
            pass

    def _update_preview(self):
        r, g, b, a = self.selected_color
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.color_preview.config(bg=hex_color)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImagePainter(root)
    root.mainloop()
