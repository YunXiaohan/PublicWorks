import sys
import ctypes
import numpy as np
import cv2
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from PIL import Image, ImageTk
from vimba import Vimba, Frame, FrameStatus, PixelFormat, Camera
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK

# DLL 파일 경로를 명시적으로 로드합니다.
dll_path = r"C:\Users\Esol\Desktop\Thorlabs\Scientific Camera Interfaces\SDK\Native Toolkit\dlls\Native_64_lib\thorlabs_tsi_camera_sdk.dll"
ctypes.CDLL(dll_path)

# TSI SDK의 설치 경로를 Python 경로에 추가합니다.
sdk_path = r"C:\Users\Esol\Desktop\Thorlabs\Scientific Camera Interfaces\SDK\Python Camera Toolkit\source"
sys.path.append(sdk_path)

ThorCam_최소값 = 0  # 기본 최소값
ThorCam_최대값 = 1023  # 기본 최대값
MakoCam_최소값 = 0  # 기본 최소값
MakoCam_최대값 = 1023  # 기본 최대값
ThorCam_노출시간 = 50  # us (ThorCam 노출 시간)
MakoCam_노출시간 = 50  # us (MakoCam 노출 시간)
VGX_WIDTH = 800  # 축소할 너비
VGX_HEIGHT = 600  # 축소할 높이

class DualCameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dual Camera Viewer")
        self.root.geometry("1750x1200")
        self.root.configure(background="#2e2e2e")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TLabel", background="#2e2e2e", foreground="#ffffff", font=("Helvetica", 12))
        style.configure("Info.TLabel", font=("Helvetica", 14, "bold"), foreground="#00ff00")
        style.configure("Title.TLabel", font=("Helvetica", 16, "bold"), foreground="#ff9900")
        style.configure("TButton", background="#444444", foreground="#ffffff", font=("Helvetica", 12))
        style.configure("Console.TText", background="#000000", foreground="#00ff00", font=("Helvetica", 14))

        self.main_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.bottom_frame = ttk.Frame(self.main_frame)
        self.bottom_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.create_thorcam_widgets()
        self.create_makocam_widgets()
        self.create_console()

        self.sdk = TLCameraSDK()
        self.thor_camera = None
        self.vimba = Vimba.get_instance()
        self.mako_camera = None
        self.thor_image = None
        self.mako_image = None
        self.raw_image = None

        self.setup_thor_camera()
        self.setup_mako_camera()
        self.create_settings_controls()
        self.update_frames()

        self.left_video_frame.bind("<Motion>", self.show_thor_intensity_real_time)
        self.right_video_frame.bind("<Motion>", self.show_mako_intensity_real_time)

    def create_thorcam_widgets(self):
        self.left_video_frame = ttk.Label(self.left_frame, relief="solid")
        self.left_video_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.left_title_label = ttk.Label(self.left_frame, text="Thor Cam", style="Title.TLabel")
        self.left_title_label.pack(fill=tk.X, padx=10, pady=5)

        self.left_info_label_click = ttk.Label(self.left_frame, text="Click Pixel Info: ", style="Info.TLabel")
        self.left_info_label_click.pack(fill=tk.X, padx=10, pady=5)

        self.left_info_label_move = ttk.Label(self.left_frame, text="Move Pixel Info: ", style="Info.TLabel")
        self.left_info_label_move.pack(fill=tk.X, padx=10, pady=5)

    def create_makocam_widgets(self):
        self.right_video_frame = ttk.Label(self.right_frame, relief="solid")
        self.right_video_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.right_title_label = ttk.Label(self.right_frame, text="Mako Cam", style="Title.TLabel")
        self.right_title_label.pack(fill=tk.X, padx=10, pady=5)

        self.right_info_label_click = ttk.Label(self.right_frame, text="Click Pixel Info: ", style="Info.TLabel")
        self.right_info_label_click.pack(fill=tk.X, padx=10, pady=5)

        self.right_info_label_move = ttk.Label(self.right_frame, text="Move Pixel Info: ", style="Info.TLabel")
        self.right_info_label_move.pack(fill=tk.X, padx=10, pady=5)

    def create_console(self):
        self.console_output = scrolledtext.ScrolledText(self.bottom_frame, wrap=tk.WORD, width=150, height=10, state='disabled', background="#000000", foreground="#00ff00", font=("Helvetica", 14))
        self.console_output.grid(row=4, column=0, columnspan=6, padx=10, pady=10, sticky="ew")

    def log_message(self, message):
        self.console_output.config(state='normal')
        self.console_output.insert(tk.END, message + '\n')
        self.console_output.config(state='disabled')
        self.console_output.yview(tk.END)

    def create_settings_controls(self):
        ttk.Label(self.bottom_frame, text="ThorCam Exposure (us):", style="TLabel").grid(row=0, column=0, padx=5, pady=5)
        self.thor_exposure_entry = ttk.Entry(self.bottom_frame)
        self.thor_exposure_entry.grid(row=0, column=1, padx=5, pady=5)
        self.thor_exposure_entry.insert(0, str(ThorCam_노출시간))
        ttk.Button(self.bottom_frame, text="Set", command=self.set_thor_exposure).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(self.bottom_frame, text="MakoCam Exposure (us):", style="TLabel").grid(row=0, column=3, padx=5, pady=5)
        self.mako_exposure_entry = ttk.Entry(self.bottom_frame)
        self.mako_exposure_entry.grid(row=0, column=4, padx=5, pady=5)
        self.mako_exposure_entry.insert(0, str(MakoCam_노출시간))
        ttk.Button(self.bottom_frame, text="Set", command=self.set_mako_exposure).grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(self.bottom_frame, text="ThorCam Min:", style="TLabel").grid(row=1, column=0, padx=5, pady=5)
        self.thor_min_entry = ttk.Entry(self.bottom_frame)
        self.thor_min_entry.grid(row=1, column=1, padx=5, pady=5)
        self.thor_min_entry.insert(0, str(ThorCam_최소값))
        ttk.Label(self.bottom_frame, text="ThorCam Max:", style="TLabel").grid(row=1, column=2, padx=5, pady=5)
        self.thor_max_entry = ttk.Entry(self.bottom_frame)
        self.thor_max_entry.grid(row=1, column=3, padx=5, pady=5)
        self.thor_max_entry.insert(0, str(ThorCam_최대값))
        ttk.Button(self.bottom_frame, text="Set", command=self.set_thor_min_max).grid(row=1, column=4, padx=5, pady=5)

        ttk.Label(self.bottom_frame, text="MakoCam Min:", style="TLabel").grid(row=2, column=0, padx=5, pady=5)
        self.mako_min_entry = ttk.Entry(self.bottom_frame)
        self.mako_min_entry.grid(row=2, column=1, padx=5, pady=5)
        self.mako_min_entry.insert(0, str(MakoCam_최소값))
        ttk.Label(self.bottom_frame, text="MakoCam Max:", style="TLabel").grid(row=2, column=2, padx=5, pady=5)
        self.mako_max_entry = ttk.Entry(self.bottom_frame)
        self.mako_max_entry.grid(row=2, column=3, padx=5, pady=5)
        self.mako_max_entry.insert(0, str(MakoCam_최대값))
        ttk.Button(self.bottom_frame, text="Set", command=self.set_mako_min_max).grid(row=2, column=4, padx=5, pady=5)

        ttk.Button(self.bottom_frame, text="Save ThorCam Raw Data", command=self.save_thor_raw_data).grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        ttk.Button(self.bottom_frame, text="Save MakoCam Raw Data", command=self.save_mako_raw_data).grid(row=3, column=2, columnspan=2, padx=5, pady=5)

    def setup_thor_camera(self):
        camera_list = self.sdk.discover_available_cameras()
        if len(camera_list) == 0:
            self.log_message("No ThorCam cameras detected")
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
            self.log_message("No MAKO cameras detected")
            return

        self.mako_camera = cameras[0]
        self.mako_camera.__enter__()

        self.mako_camera.set_pixel_format(PixelFormat.Mono10)
        self.mako_camera.Width = 1600
        self.mako_camera.Height = 1200
        self.mako_camera.OffsetX = 0
        self.mako_camera.OffsetY = 0

        self.set_mako_exposure(MakoCam_노출시간)
        self.mako_camera.BlackLevel = 1.0

        frame = self.mako_camera.get_frame()
        self.mako_camera.queue_frame(frame)
        self.mako_camera.start_streaming(self.mako_frame_callback)
        self.right_video_frame.bind("<Button-1>", self.show_mako_intensity)

    def set_thor_exposure(self):
        try:
            exposure_time = int(self.thor_exposure_entry.get())
            self.thor_camera.exposure_time_us = exposure_time
            self.log_message(f"ThorCam exposure time set to {exposure_time} us")
        except Exception as e:
            self.log_message(f"Failed to set ThorCam exposure time: {e}")

    def set_mako_exposure(self, exposure_time=None):
        if exposure_time is None:
            try:
                exposure_time = int(self.mako_exposure_entry.get())
            except ValueError:
                self.log_message("Invalid MakoCam exposure time")
                return
        try:
            exposure_feature = self.mako_camera.get_feature_by_name('ExposureTimeAbs')
            exposure_feature.set(exposure_time)
            self.log_message(f"MakoCam exposure time set to {exposure_time} us")
        except Exception as e:
            self.log_message(f"Failed to set MakoCam exposure time: {e}")

    def set_thor_min_max(self):
        try:
            global ThorCam_최소값, ThorCam_최대값
            ThorCam_최소값 = int(self.thor_min_entry.get())
            ThorCam_최대값 = int(self.thor_max_entry.get())
            self.log_message(f"ThorCam min/max set to {ThorCam_최소값}/{ThorCam_최대값}")
        except Exception as e:
            self.log_message(f"Failed to set ThorCam min/max: {e}")

    def set_mako_min_max(self):
        try:
            global MakoCam_최소값, MakoCam_최대값
            MakoCam_최소값 = int(self.mako_min_entry.get())
            MakoCam_최대값 = int(self.mako_max_entry.get())
            self.log_message(f"MakoCam min/max set to {MakoCam_최소값}/{MakoCam_최대값}")
        except Exception as e:
            self.log_message(f"Failed to set MakoCam min/max: {e}")

    def show_thor_intensity(self, event):
        if self.thor_image is not None:
            x = int(event.x * self.thor_image.shape[1] / VGX_WIDTH)
            y = int(event.y * self.thor_image.shape[0] / VGX_HEIGHT)
            if x < self.thor_image.shape[1] and y < self.thor_image.shape[0]:
                intensity = self.thor_image[y, x]
                self.left_info_label_click.config(text=f"Click Pixel Info: X: {x}, Y: {y}, Intensity: {intensity}")

    def show_mako_intensity(self, event):
        if self.raw_image is not None:
            x = int(event.x * self.raw_image.shape[1] / VGX_WIDTH)
            y = int(event.y * self.raw_image.shape[0] / VGX_HEIGHT)
            if x < self.raw_image.shape[1] and y < self.raw_image.shape[0]:
                intensity = self.raw_image[y, x].item()
                self.right_info_label_click.config(text=f"Click Pixel Info: X: {x}, Y: {y}, Intensity: {intensity}")

    def show_thor_intensity_real_time(self, event):
        if self.thor_image is not None:
            x = int(event.x * self.thor_image.shape[1] / VGX_WIDTH)
            y = int(event.y * self.thor_image.shape[0] / VGX_HEIGHT)
            if x < self.thor_image.shape[1] and y < self.thor_image.shape[0]:
                intensity = self.thor_image[y, x]
                self.left_info_label_move.config(text=f"Move Pixel Info: X: {x}, Y: {y}, Intensity: {intensity}")

    def show_mako_intensity_real_time(self, event):
        if self.raw_image is not None:
            x = int(event.x * self.raw_image.shape[1] / VGX_WIDTH)
            y = int(event.y * self.raw_image.shape[0] / VGX_HEIGHT)
            if x < self.raw_image.shape[1] and y < self.raw_image.shape[0]:
                intensity = self.raw_image[y, x].item()
                self.right_info_label_move.config(text=f"Move Pixel Info: X: {x}, Y: {y}, Intensity: {intensity}")

    def mako_frame_callback(self, cam: Camera, frame: Frame):
        if frame.get_status() == FrameStatus.Complete:
            image = frame.as_numpy_ndarray()
            if frame.get_pixel_format() == PixelFormat.Mono10:
                image = np.squeeze(image)
                intensity_image = np.clip(image, MakoCam_최소값, MakoCam_최대값)
                self.raw_image = intensity_image
                image_8bit = (intensity_image >> 2).astype(np.uint8)
                image_colormap = cv2.applyColorMap(image_8bit, cv2.COLORMAP_JET)
                self.mako_image = image_colormap
            cam.queue_frame(frame)

    def update_frames(self):
        frame = self.thor_camera.get_pending_frame_or_null()
        if frame is not None:
            self.thor_image = frame.image_buffer.copy()
            image_clipped = np.clip(self.thor_image, ThorCam_최소값, ThorCam_최대값)
            image_8bit = ((image_clipped - ThorCam_최소값) / (ThorCam_최대값 - ThorCam_최소값) * 255).astype(np.uint8)
            image_colormap = cv2.applyColorMap(image_8bit, cv2.COLORMAP_JET)
            image_rgb = cv2.cvtColor(image_colormap, cv2.COLOR_BGR2RGB)
            image_resized = cv2.resize(image_rgb, (VGX_WIDTH, VGX_HEIGHT))
            image_pil = Image.fromarray(image_resized)
            image_tk = ImageTk.PhotoImage(image_pil)
            self.left_video_frame.imgtk = image_tk
            self.left_video_frame.config(image=image_tk)

        if self.mako_image is not None:
            image_clipped = np.clip(self.raw_image, MakoCam_최소값, MakoCam_최대값)
            image_8bit = ((image_clipped - MakoCam_최소값) / (MakoCam_최대값 - MakoCam_최소값) * 255).astype(np.uint8)
            image_colormap = cv2.applyColorMap(image_8bit, cv2.COLORMAP_JET)
            image_rgb = cv2.cvtColor(image_colormap, cv2.COLOR_BGR2RGB)
            image_resized = cv2.resize(image_rgb, (VGX_WIDTH, VGX_HEIGHT))
            image_pil = Image.fromarray(image_resized)
            image_tk = ImageTk.PhotoImage(image_pil)
            self.right_video_frame.imgtk = image_tk
            self.right_video_frame.config(image=image_tk)

        self.root.after(10, self.update_frames)

    def save_thor_raw_data(self):
        if self.thor_image is not None:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
            if file_path:
                try:
                    if self.thor_image.ndim == 2:
                        with open(file_path, 'w', encoding='utf-8') as file:
                            for row in self.thor_image:
                                file.write(' '.join(map(str, row)) + '\n')
                        self.log_message(f"Saved ThorCam raw data to {file_path}")
                    else:
                        self.log_message("Failed to save ThorCam raw data: Image is not 2D")
                except Exception as e:
                    self.log_message(f"Error saving ThorCam raw data: {e}")

    def save_mako_raw_data(self):
        if self.raw_image is not None:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
            if file_path:
                if self.raw_image.ndim == 2:
                    np.savetxt(file_path, self.raw_image, fmt='%d')
                    self.log_message(f"Saved MakoCam raw data to {file_path}")
                else:
                    self.log_message("Failed to save MakoCam raw data: Image is not 2D")

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
