import sys
import numpy as np
import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from vimba import Vimba, Frame, FrameStatus, PixelFormat, Camera

class MakoCameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MAKO G192B Viewer")

        self.video_frame = ttk.Label(self.root)
        self.video_frame.grid(row=0, column=0, padx=10, pady=10)

        self.info_label = ttk.Label(self.root, text="Pixel Info: ")
        self.info_label.grid(row=1, column=0, padx=10, pady=10)

        self.vimba = Vimba.get_instance()
        self.mako_camera = None
        self.image = None
        self.raw_image = None

        self.setup_camera()
        self.update_frame()

    def setup_camera(self):
        self.vimba.__enter__()
        cameras = self.vimba.get_all_cameras()
        if not cameras:
            print("No MAKO cameras detected")
            return

        self.mako_camera = cameras[0]
        self.mako_camera.__enter__()

        # 픽셀 포맷을 Mono10으로 설정
        self.mako_camera.set_pixel_format(PixelFormat.Mono10)

        # ROI 설정 (Width, Height, OffsetX, OffsetY)
        self.mako_camera.Width = 1600
        self.mako_camera.Height = 1200
        self.mako_camera.OffsetX = 0
        self.mako_camera.OffsetY = 0

        self.mako_camera.ExposureTimeAbs = 4950.0
        self.mako_camera.BlackLevel = 1.0

        frame = self.mako_camera.get_frame()
        self.mako_camera.queue_frame(frame)

        self.mako_camera.start_streaming(self.frame_callback)
        self.video_frame.bind("<Button-1>", self.show_intensity)

    def show_intensity(self, event):
        if self.raw_image is not None:
            x = event.x
            y = event.y
            if x < self.raw_image.shape[1] and y < self.raw_image.shape[0]:
                intensity = self.raw_image[y, x]
                self.info_label.config(text=f"Pixel Info: X: {x}, Y: {y}, Intensity: {intensity}")

    def frame_callback(self, cam: Camera, frame: Frame):
        if frame.get_status() == FrameStatus.Complete:
            image = frame.as_numpy_ndarray()
            if frame.get_pixel_format() == PixelFormat.Mono10:
                # Mono10 포맷의 값을 10비트에서 8비트로 축소하여 Jet 컬러맵 적용
                intensity_image = np.clip(image, 0, 1023)
                self.raw_image = intensity_image  # Save raw image for intensity calculation
                image_8bit = (intensity_image >> 2).astype(np.uint8)  # Convert to 8-bit
                image_colormap = cv2.applyColorMap(image_8bit, cv2.COLORMAP_JET)
                self.image = image_colormap
            cam.queue_frame(frame)

    def update_frame(self):
        if self.image is not None:
            image_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            image_pil = Image.fromarray(image_rgb)
            image_tk = ImageTk.PhotoImage(image_pil)
            self.video_frame.imgtk = image_tk
            self.video_frame.config(image=image_tk)

        self.root.after(10, self.update_frame)

    def on_closing(self):
        if self.mako_camera:
            self.mako_camera.stop_streaming()
            self.mako_camera.__exit__(None, None, None)
        self.vimba.__exit__(None, None, None)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MakoCameraApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
