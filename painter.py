import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
import numpy as np
import random

class ImagePainter:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Image Painter")

        # Images
        self.original_background = None
        self.original_foreground = None
        self.background = None
        self.foreground = None
        self.bg_image = None
        self.fg_image = None
        self.composite_image = None

        # Foreground position
        self.fg_x = 0
        self.fg_y = 0

        # Background position
        self.bg_x = 0
        self.bg_y = 0

        # Result size tracking
        self.result_width = None
        self.result_height = None
        self.result_x = 0
        self.result_y = 0
        self.display_offset_x = 0
        self.display_offset_y = 0

        # UI elements
        self.load_bg_button = tk.Button(root, text="Load Background", command=self.load_background)
        self.load_bg_button.pack()

        self.load_fg_button = tk.Button(root, text="Load Foreground", command=self.load_foreground)
        self.load_fg_button.pack()

        # Resize controls
        resize_frame = tk.Frame(root)
        resize_frame.pack()

        tk.Label(resize_frame, text="Width:").grid(row=0, column=0)
        self.width_entry = tk.Entry(resize_frame)
        self.width_entry.grid(row=0, column=1)

        tk.Label(resize_frame, text="Height:").grid(row=1, column=0)
        self.height_entry = tk.Entry(resize_frame)
        self.height_entry.grid(row=1, column=1)

        tk.Button(resize_frame, text="Resize BG", command=self.resize_background).grid(row=2, column=0)
        tk.Button(resize_frame, text="Resize FG", command=self.resize_foreground).grid(row=2, column=1)
        tk.Button(resize_frame, text="Resize Result", command=self.resize_result).grid(row=2, column=2)
        tk.Button(resize_frame, text="Save Result", command=self.save_result).grid(row=2, column=3)

        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack()

        # Add scrollbars
        self.h_scroll = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll = tk.Scrollbar(root, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        # Bind mouse events for dragging foreground
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)

        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Drag mode dropdown
        drag_frame = tk.Frame(root)
        drag_frame.pack()
        tk.Label(drag_frame, text="Drag Mode:").pack(side=tk.LEFT)
        self.drag_mode = tk.StringVar(value="Foreground")
        self.drag_dropdown = tk.OptionMenu(drag_frame, self.drag_mode, "Foreground", "Background", "Result")
        self.drag_dropdown.pack(side=tk.LEFT)

        # View mode dropdown
        view_frame = tk.Frame(root)
        view_frame.pack()
        tk.Label(view_frame, text="View Mode:").pack(side=tk.LEFT)
        self.view_mode = tk.StringVar(value="BGR")
        self.view_dropdown = tk.OptionMenu(view_frame, self.view_mode, "BGR", "Grayscale", "Binary", "Contours", command=self.on_view_change)
        self.view_dropdown.pack(side=tk.LEFT)

        # Info label
        self.info_label = tk.Label(root, text="No images loaded", justify=tk.LEFT)
        self.info_label.pack()

        # Contour info label
        self.contour_info_label = tk.Label(root, text="", justify=tk.LEFT)
        self.contour_info_label.pack()

    def load_background(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if file_path:
            self.original_background = Image.open(file_path).convert('RGBA')
            self.background = self.original_background.copy()
            self.result_width = None
            self.result_height = None
            self.result_x = 0
            self.result_y = 0
            self.update_display()
            self.update_info()

    def load_foreground(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if file_path:
            self.original_foreground = Image.open(file_path).convert('RGBA')
            self.foreground = self.original_foreground.copy()
            self.result_width = None
            self.result_height = None
            self.result_x = 0
            self.result_y = 0
            self.update_display()
            self.update_info()

    def update_display(self):
        self.canvas.delete("all")
        if self.background and self.foreground:
            bg_copy = self.background.copy()
            result_w = self.result_width if self.result_width else bg_copy.width
            result_h = self.result_height if self.result_height else bg_copy.height
            min_x = min(0, int(self.bg_x), int(self.fg_x), int(self.result_x))
            min_y = min(0, int(self.bg_y), int(self.fg_y), int(self.result_y))
            max_x = max(int(self.bg_x + bg_copy.width), int(self.fg_x + self.foreground.width), int(self.result_x + result_w), 0)
            max_y = max(int(self.bg_y + bg_copy.height), int(self.fg_y + self.foreground.height), int(self.result_y + result_h), 0)
            width = max_x - min_x
            height = max_y - min_y
            self.display_offset_x = -min_x
            self.display_offset_y = -min_y
            composite = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            composite.paste(bg_copy, (int(self.bg_x - min_x), int(self.bg_y - min_y)))
            mask = self.foreground.split()[-1]
            composite.paste(self.foreground, (int(self.fg_x - min_x), int(self.fg_y - min_y)), mask)
            if self.view_mode.get() == "Grayscale":
                composite = composite.convert('L')
            elif self.view_mode.get() == "Binary":
                composite = composite.convert('L').point(lambda p: 0 if p < 127 else 255)
            elif self.view_mode.get() == "Contours":
                # Convert to binary
                binary = composite.convert('L').point(lambda p: 0 if p < 127 else 255)
                # Convert to cv2
                binary_np = np.array(binary)
                # Find contours
                contours, _ = cv2.findContours(binary_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                # Create color image
                color_img = np.zeros((binary_np.shape[0], binary_np.shape[1], 3), dtype=np.uint8)
                # Draw filled contours with random colors
                for contour in contours:
                    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                    cv2.fillPoly(color_img, [contour], color)
                # Convert BGR to RGB for PIL
                color_img = cv2.cvtColor(color_img, cv2.COLOR_BGR2RGB)
                # Convert back to PIL
                composite = Image.fromarray(color_img)
                # Update contour info
                num_contours = len(contours)
                total_area = sum(cv2.contourArea(c) for c in contours)
                self.contour_info_label.config(text=f"Contours: {num_contours}, Total area: {total_area:.0f}px²")
            else:
                self.contour_info_label.config(text="")
            self.composite_image = ImageTk.PhotoImage(composite)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.composite_image)
            if self.result_width and self.result_height:
                rect_x0 = int(self.result_x + self.display_offset_x)
                rect_y0 = int(self.result_y + self.display_offset_y)
                rect_x1 = rect_x0 + self.result_width
                rect_y1 = rect_y0 + self.result_height
                self.canvas.create_rectangle(rect_x0, rect_y0, rect_x1, rect_y1, outline="red", width=2)
            self.canvas.config(scrollregion=(0, 0, width, height))
        elif self.background:
            bg_copy = self.background.copy()
            min_x = min(0, int(self.bg_x))
            min_y = min(0, int(self.bg_y))
            max_x = max(int(self.bg_x + bg_copy.width), 0)
            max_y = max(int(self.bg_y + bg_copy.height), 0)
            width = max_x - min_x
            height = max_y - min_y
            composite = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            composite.paste(bg_copy, (int(max(0, self.bg_x - min_x)), int(max(0, self.bg_y - min_y))))
            if self.view_mode.get() == "Grayscale":
                composite = composite.convert('L')
            elif self.view_mode.get() in ["Binary", "Contours"]:
                composite = composite.convert('L').point(lambda p: 0 if p < 127 else 255)
            self.composite_image = ImageTk.PhotoImage(composite)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.composite_image)
            self.canvas.config(scrollregion=(0, 0, width, height))
        elif self.foreground:
            fg_copy = self.foreground.copy()
            if self.view_mode.get() == "Grayscale":
                fg_copy = fg_copy.convert('L')
            elif self.view_mode.get() in ["Binary", "Contours"]:
                fg_copy = fg_copy.convert('L').point(lambda p: 0 if p < 127 else 255)
            self.composite_image = ImageTk.PhotoImage(fg_copy)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.composite_image)
            self.canvas.config(scrollregion=(0, 0, self.foreground.width, self.foreground.height))
        else:
            self.canvas.config(scrollregion=(0, 0, 800, 600))

    def start_drag(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        scene_x = canvas_x - self.display_offset_x
        scene_y = canvas_y - self.display_offset_y
        mode = self.drag_mode.get()
        if mode == "Result" and self.result_width and self.result_height:
            rect_x0 = self.result_x
            rect_y0 = self.result_y
            rect_x1 = rect_x0 + self.result_width
            rect_y1 = rect_y0 + self.result_height
            if rect_x0 <= scene_x <= rect_x1 and rect_y0 <= scene_y <= rect_y1:
                self.dragging = True
                self.drag_start_x = scene_x - self.result_x
                self.drag_start_y = scene_y - self.result_y
        elif mode == "Foreground" and self.foreground:
            self.dragging = True
            self.drag_start_x = scene_x - self.fg_x
            self.drag_start_y = scene_y - self.fg_y
        elif mode == "Background" and self.background:
            self.dragging = True
            self.drag_start_x = scene_x - self.bg_x
            self.drag_start_y = scene_y - self.bg_y

    def drag(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        scene_x = canvas_x - self.display_offset_x
        scene_y = canvas_y - self.display_offset_y
        mode = self.drag_mode.get()
        if mode == "Result" and self.dragging:
            self.result_x = scene_x - self.drag_start_x
            self.result_y = scene_y - self.drag_start_y
            self.update_display()
            self.update_info()
        elif mode == "Foreground" and self.dragging and self.foreground:
            self.fg_x = scene_x - self.drag_start_x
            self.fg_y = scene_y - self.drag_start_y
            self.update_display()
            self.update_info()
        elif mode == "Background" and self.dragging and self.background:
            self.bg_x = scene_x - self.drag_start_x
            self.bg_y = scene_y - self.drag_start_y
            self.update_display()
            self.update_info()

    def end_drag(self, event):
        self.dragging = False

    def on_view_change(self, value):
        self.update_display()

    def resize_background(self):
        if self.original_background:
            try:
                width = int(self.width_entry.get())
                height = int(self.height_entry.get())
                self.background = self.original_background.resize((width, height), Image.LANCZOS)
                self.update_display()
                self.update_info()
            except ValueError:
                pass  # Invalid input

    def resize_foreground(self):
        if self.original_foreground:
            try:
                width = int(self.width_entry.get())
                height = int(self.height_entry.get())
                self.foreground = self.original_foreground.resize((width, height), Image.LANCZOS)
                self.update_display()
                self.update_info()
            except ValueError:
                pass

    def resize_result(self):
        if self.background and self.foreground:
            try:
                width = int(self.width_entry.get())
                height = int(self.height_entry.get())
                self.result_width = width
                self.result_height = height
                self.result_x = 0 if self.result_x is None else self.result_x
                self.result_y = 0 if self.result_y is None else self.result_y
                self.update_display()
                self.update_info()
            except ValueError:
                pass

    def get_result_image(self):
        if not (self.background and self.foreground):
            return None
        bg_copy = self.background.copy()
        result_w = self.result_width if self.result_width else bg_copy.width
        result_h = self.result_height if self.result_height else bg_copy.height
        min_x = min(0, int(self.bg_x), int(self.fg_x), int(self.result_x))
        min_y = min(0, int(self.bg_y), int(self.fg_y), int(self.result_y))
        width = int(max(int(self.bg_x + bg_copy.width), int(self.fg_x + self.foreground.width), int(self.result_x + result_w), 0) - min_x)
        height = int(max(int(self.bg_y + bg_copy.height), int(self.fg_y + self.foreground.height), int(self.result_y + result_h), 0) - min_y)
        composite = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        composite.paste(bg_copy, (int(self.bg_x - min_x), int(self.bg_y - min_y)))
        mask = self.foreground.split()[-1]
        composite.paste(self.foreground, (int(self.fg_x - min_x), int(self.fg_y - min_y)), mask)
        if self.result_width and self.result_height:
            crop_left = int(self.result_x - min_x)
            crop_top = int(self.result_y - min_y)
            crop_right = crop_left + self.result_width
            crop_bottom = crop_top + self.result_height
            composite = composite.crop((crop_left, crop_top, crop_right, crop_bottom))
        return composite

    def save_result(self):
        image = self.get_result_image()
        if image is None:
            return
        file_path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG', '*.png'), ('JPEG', '*.jpg;*.jpeg'), ('BMP', '*.bmp')])
        if file_path:
            if file_path.lower().endswith(('.jpg', '.jpeg')):
                image = image.convert('RGB')
            image.save(file_path)

    def update_info(self):
        info_text = ""
        if self.background:
            bg_size = (self.background.width, self.background.height)
            bg_offset = f" (offset: {int(self.bg_x)}, {int(self.bg_y)})" if self.bg_x != 0 or self.bg_y != 0 else ""
            info_text += f"Background: {bg_size[0]}x{bg_size[1]}px{bg_offset}\n"
        if self.foreground:
            fg_size = (self.foreground.width, self.foreground.height)
            fg_offset = f" (offset: {int(self.fg_x)}, {int(self.fg_y)})" if self.fg_x != 0 or self.fg_y != 0 else ""
            info_text += f"Foreground: {fg_size[0]}x{fg_size[1]}px{fg_offset}\n"
        if self.background and self.foreground:
            if self.result_width and self.result_height:
                result_size = (self.result_width, self.result_height)
                result_offset = f" (offset: {int(self.result_x)}, {int(self.result_y)})"
            else:
                result_size = (self.background.width, self.background.height)
                result_offset = ""
            info_text += f"Result: {result_size[0]}x{result_size[1]}px{result_offset}"
        if not info_text:
            info_text = "No images loaded"
        self.info_label.config(text=info_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImagePainter(root)
    root.mainloop()