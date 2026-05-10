import tkinter as tk
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

        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack()

        self.h_scroll = tk.Scrollbar(root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll = tk.Scrollbar(root, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)

        self.dragging = False

        view_frame = tk.Frame(root)
        view_frame.pack()
        tk.Label(view_frame, text="View Mode:").pack(side=tk.LEFT)
        self.view_mode = tk.StringVar(value="BGR")
        self.view_dropdown = tk.OptionMenu(
            view_frame, self.view_mode, "BGR", "Grayscale", "Binary", "Contours",
            command=self.on_view_change
        )
        self.view_dropdown.pack(side=tk.LEFT)

        self.info_label = tk.Label(root, text="No image loaded", justify=tk.LEFT)
        self.info_label.pack()

        self.contour_info_label = tk.Label(root, text="", justify=tk.LEFT)
        self.contour_info_label.pack()

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")])
        if file_path:
            self.original_image = Image.open(file_path).convert('RGBA')
            self.image = self.original_image.copy()
            self.update_display()
            self.update_info()

    def update_display(self):
        self.canvas.delete("all")
        if not self.image:
            self.canvas.config(scrollregion=(0, 0, 800, 600))
            return

        composite = self.image.copy()

        view = self.view_mode.get()
        if view == "Grayscale":
            composite = composite.convert('L')
        elif view == "Binary":
            composite = composite.convert('L').point(lambda p: 0 if p < 127 else 255)
        elif view == "Contours":
            binary = composite.convert('L').point(lambda p: 0 if p < 127 else 255)
            binary_np = np.array(binary)
            contours, _ = cv2.findContours(binary_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            color_img = np.zeros((binary_np.shape[0], binary_np.shape[1], 3), dtype=np.uint8)
            for contour in contours:
                color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                cv2.fillPoly(color_img, [contour], color)
            color_img = cv2.cvtColor(color_img, cv2.COLOR_BGR2RGB)
            composite = Image.fromarray(color_img)
            num_contours = len(contours)
            total_area = sum(cv2.contourArea(c) for c in contours)
            self.contour_info_label.config(text=f"Contours: {num_contours}, Total area: {total_area:.0f}px²")
        else:
            self.contour_info_label.config(text="")

        self.display_image = ImageTk.PhotoImage(composite)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.display_image)
        self.canvas.config(scrollregion=(0, 0, composite.width, composite.height))

    def start_drag(self, event):
        if not self.image:
            return
        self.canvas.scan_mark(event.x, event.y)
        self.dragging = True

    def drag(self, event):
        if not self.dragging:
            return
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_view_change(self, value):
        self.update_display()

    def resize_image(self):
        if self.original_image:
            try:
                width = int(self.width_entry.get())
                height = int(self.height_entry.get())
                self.image = self.original_image.resize((width, height), Image.LANCZOS)
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

    def update_info(self):
        if self.image:
            size = (self.image.width, self.image.height)
            self.info_label.config(text=f"Image: {size[0]}x{size[1]}px")
        else:
            self.info_label.config(text="No image loaded")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImagePainter(root)
    root.mainloop()
