import sys
import ctypes
import numpy as np
import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from vimba import Vimba, Frame, FrameStatus, PixelFormat, Camera
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK

# DLL 파일 경로를 명시적으로 로드합니다.
dll_path = r"C:\Users\Esol\Desktop\Thorlabs\Scientific Camera Interfaces\SDK\Native Toolkit\dlls\Native_64_lib\thorlabs_tsi_camera_sdk.dll"
ctypes.CDLL(dll_path)

# TSI SDK의 설치 경로를 Python 경로에 추가합니다.
sdk_path = r"C:\Users\Esol\Desktop\Thorlabs\Scientific Camera Interfaces\SDK\Python Camera Toolkit\source"
sys.path.append(sdk_path)

최소값 = 0  # 값
최대값 = 1023  # 값
ThorCam_노출시간 = 50  # us (ThorCam 노출 시간)
MakoCam_노출시간 = 100  # us (MakoCam 노출 시간)
VGX_WIDTH = 800  # 축소할 너비
VGX_HEIGHT = 600  # 축소할 높이

class DualCameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dual Camera Viewer")
        self.root.geometry("1920x1080")
        self.root.configure(background="#2e2e2e")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TLabel", background="#2e2e2e", foreground="#ffffff", font=("Helvetica", 12))
        style.configure("Info.TLabel", font=("Helvetica", 14, "bold"), foreground="#00ff00")
        style.configure("Title.TLabel", font=("Helvetica", 16, "bold"), foreground="#ff9900")

        self.main_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.left_video_frame = ttk.Label(self.left_frame, relief="solid")
        self.left_video_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.right_video_frame = ttk.Label(self.right_frame, relief="solid")
        self.right_video_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.left_title_label = ttk.Label(self.left_frame, text="Thor Cam", style="Title.TLabel")
        self.left_title_label.pack(fill=tk.X, padx=10, pady=5)

        self.right_title_label = ttk.Label(self.right_frame, text="Mako Cam", style="Title.TLabel")
        self.right_title_label.pack(fill=tk.X, padx=10, pady=5)

        self.left_info_label = ttk.Label(self.left_frame, text="Pixel Info: ", style="Info.TLabel")
        self.left_info_label.pack(fill=tk.X, padx=10, pady=5)

        self.right_info_label = ttk.Label(self.right_frame, text="Pixel Info: ", style="Info.TLabel")
        self.right_info_label.pack(fill=tk.X, padx=10, pady=5)

        self.sdk = TLCameraSDK()
        self.thor_camera = None
        self.vimba = Vimba.get_instance()
        self.mako_camera = None
        self.thor_image = None
        self.mako_image = None
        self.raw_image = None

        self.setup_thor_camera()
        self.setup_mako_camera()
        self.update_frames()

    def setup_thor_camera(self):
        camera_list = self.sdk.discover_available_cameras()
        if len(camera_list) == 0:
            print("No ThorCam cameras detected")
            return

        self.thor_camera = self.sdk.open_camera(camera_list[0])
        self.thor_camera.frames_per_trigger_zero_for_unlimited = 0
        self.thor_camera.exposure_time_us = ThorCam_노출시간
        self.thor_camera.gain = 0
        self.thor_camera.black_level = 1
        self.thor_camera.arm(2)
        self.thor_camera.issue_software_trigger()

        self.left_video_frame.bind("<Button-1>", self.show_thor_intensity)

    def setup_mako_camera(self):
        self.vimba.__enter__()
        cameras = self.vimba.get_all_cameras()
        if not cameras:
            print("No MAKO cameras detected")
            return

        self.mako_camera = cameras[0]
        self.mako_camera.__enter__()

        self.mako_camera.set_pixel_format(PixelFormat.Mono10)
        self.mako_camera.Width = 1600
        self.mako_camera.Height = 1200
        self.mako_camera.OffsetX = 0
        self.mako_camera.OffsetY = 0
        self.mako_camera.ExposureTimeAbs = MakoCam_노출시간
        self.mako_camera.BlackLevel = 1.0

        frame = self.mako_camera.get_frame()
        self.mako_camera.queue_frame(frame)
        self.mako_camera.start_streaming(self.mako_frame_callback)
        self.right_video_frame.bind("<Button-1>", self.show_mako_intensity)

    def show_thor_intensity(self, event):
        if self.thor_image is not None:
            x = int(event.x * self.thor_image.shape[1] / VGX_WIDTH)
            y = int(event.y * self.thor_image.shape[0] / VGX_HEIGHT)
            if x < self.thor_image.shape[1] and y < self.thor_image.shape[0]:
                intensity = self.thor_image[y, x]
                self.left_info_label.config(text=f"Pixel Info: X: {x}, Y: {y}, Intensity: {intensity}")

    def show_mako_intensity(self, event):
        if self.raw_image is not None:
            x = int(event.x * self.raw_image.shape[1] / VGX_WIDTH)
            y = int(event.y * self.raw_image.shape[0] / VGX_HEIGHT)
            if x < self.raw_image.shape[1] and y < self.raw_image.shape[0]:
                intensity = self.raw_image[y, x].item()
                self.right_info_label.config(text=f"Pixel Info: X: {x}, Y: {y}, Intensity: {intensity}")

    def mako_frame_callback(self, cam: Camera, frame: Frame):
        if frame.get_status() == FrameStatus.Complete:
            image = frame.as_numpy_ndarray()
            if frame.get_pixel_format() == PixelFormat.Mono10:
                intensity_image = np.clip(image, 0, 1023)
                self.raw_image = intensity_image
                image_8bit = (intensity_image >> 2).astype(np.uint8)
                image_colormap = cv2.applyColorMap(image_8bit, cv2.COLORMAP_JET)
                self.mako_image = image_colormap
            cam.queue_frame(frame)

    def update_frames(self):
        # Update ThorCam frame
        frame = self.thor_camera.get_pending_frame_or_null()
        if frame is not None:
            self.thor_image = frame.image_buffer.copy()
            image_clipped = np.clip(self.thor_image, 최소값, 최대값)
            image_8bit = ((image_clipped - 최소값) / (최대값 - 최소값) * 255).astype(np.uint8)
            image_colormap = cv2.applyColorMap(image_8bit, cv2.COLORMAP_JET)
            image_rgb = cv2.cvtColor(image_colormap, cv2.COLOR_BGR2RGB)
            image_resized = cv2.resize(image_rgb, (VGX_WIDTH, VGX_HEIGHT))
            image_pil = Image.fromarray(image_resized)
            image_tk = ImageTk.PhotoImage(image_pil)
            self.left_video_frame.imgtk = image_tk
            self.left_video_frame.config(image=image_tk)

        # Update MAKO frame
        if self.mako_image is not None:
            image_rgb = cv2.cvtColor(self.mako_image, cv2.COLOR_BGR2RGB)
            image_resized = cv2.resize(image_rgb, (VGX_WIDTH, VGX_HEIGHT))
            image_pil = Image.fromarray(image_resized)
            image_tk = ImageTk.PhotoImage(image_pil)
            self.right_video_frame.imgtk = image_tk
            self.right_video_frame.config(image=image_tk)

        self.root.after(10, self.update_frames)

    def on_closing(self):
        if self.thor_camera:
            self.thor_camera.disarm()
            self.thor_camera.dispose()
        self.sdk.dispose()
        if self.mako_camera:
            self.mako_camera.stop_streaming()
            self.mako_camera.__exit__(None, None, None)
        self.vimba.__exit__(None, None, None)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DualCameraApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
