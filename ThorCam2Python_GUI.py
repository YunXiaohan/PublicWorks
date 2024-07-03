import sys
import ctypes
import numpy as np
import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# DLL 파일 경로를 명시적으로 로드합니다.
dll_path = r"C:\Users\Esol\Desktop\Thorlabs\Scientific Camera Interfaces\SDK\Native Toolkit\dlls\Native_64_lib\thorlabs_tsi_camera_sdk.dll"
ctypes.CDLL(dll_path)

# TSI SDK의 설치 경로를 Python 경로에 추가합니다.
sdk_path = r"C:\Users\Esol\Desktop\Thorlabs\Scientific Camera Interfaces\SDK\Python Camera Toolkit\source"
sys.path.append(sdk_path)

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK

최소값 = 0 # 값
최대값 = 1023 # 값
노출시간 = 0.15 # ms

class CameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ThorCam Viewer")
        
        self.video_frame = ttk.Label(self.root)
        self.video_frame.grid(row=0, column=0, padx=10, pady=10)

        self.info_label = ttk.Label(self.root, text="Pixel Info: ")
        self.info_label.grid(row=1, column=0, padx=10, pady=10)

        self.sdk = TLCameraSDK()
        self.camera = None

        self.setup_camera()
        self.update_frame()

    def setup_camera(self):
        camera_list = self.sdk.discover_available_cameras()
        if len(camera_list) == 0:
            print("No cameras detected")
            return

        self.camera = self.sdk.open_camera(camera_list[0])
        self.camera.frames_per_trigger_zero_for_unlimited = 0
        self.camera.exposure_time_us = int(노출시간 * 1000)
        self.camera.gain = 0
        self.camera.black_level = 1
        self.camera.arm(2)
        self.camera.issue_software_trigger()

        self.video_frame.bind("<Button-1>", self.show_intensity)

    def show_intensity(self, event):
        if self.image is not None:
            x = event.x
            y = event.y
            if x < self.image.shape[1] and y < self.image.shape[0]:
                intensity = self.image[y, x]
                self.info_label.config(text=f"Pixel Info: X: {x}, Y: {y}, Intensity: {intensity}")

    def update_frame(self):
        frame = self.camera.get_pending_frame_or_null()
        if frame is not None:
            self.image = frame.image_buffer.copy()

            image_clipped = np.clip(self.image, 최소값, 최대값)
            image_8bit = ((image_clipped - 최소값) / (최대값 - 최소값) * 255).astype(np.uint8)

            image_colormap = cv2.applyColorMap(image_8bit, cv2.COLORMAP_JET)
            image_rgb = cv2.cvtColor(image_colormap, cv2.COLOR_BGR2RGB)
            image_pil = Image.fromarray(image_rgb)
            image_tk = ImageTk.PhotoImage(image_pil)

            self.video_frame.imgtk = image_tk
            self.video_frame.config(image=image_tk)

        self.root.after(10, self.update_frame)

    def on_closing(self):
        if self.camera:
            self.camera.disarm()
            self.camera.dispose() 
        self.sdk.dispose()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CameraApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
