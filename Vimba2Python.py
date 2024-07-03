import cv2
import numpy as np
from vimba import Vimba, Frame, FrameStatus, PixelFormat, Camera

def frame_callback(cam: Camera, frame: Frame):
    if frame.get_status() == FrameStatus.Complete:
        # Frame을 numpy 배열로 변환
        image = frame.as_numpy_ndarray()
        
        # Mono10 형식을 처리
        if frame.get_pixel_format() == PixelFormat.Mono10:
            # 픽셀 값을 0에서 1023 사이로 제한
            image = np.clip(image, 0, 1023)
            
            # Mono10 포맷을 8비트로 축소하여 Jet 컬러맵 적용을 위함
            image = np.right_shift(image, 2)  # Mono10을 8비트로 축소
            image = ((image / 255) * 255).astype(np.uint8)
            image = cv2.applyColorMap(image, cv2.COLORMAP_JET)
        
        # OpenCV를 통해 이미지 표시
        cv2.imshow('Mako G192B', image)
        cv2.waitKey(1)
    
    # 프레임을 다시 큐에 넣어 다음 프레임을 받도록 합니다.
    cam.queue_frame(frame)

def main():
    with Vimba.get_instance() as vimba:
        cams = vimba.get_all_cameras()
        if not cams:
            raise Exception("No cameras found")
        
        with cams[0] as cam:
            # 픽셀 포맷을 Mono10으로 설정
            cam.set_pixel_format(PixelFormat.Mono10)
            
            # ROI 설정 (Width, Height, OffsetX, OffsetY)
            cam.Width = 1600
            cam.Height = 1200
            cam.OffsetX = 0
            cam.OffsetY = 0

            cam.ExposureTimeAbs = 4950.0
            cam.BlackLevel = 1.0
            
            # 프레임을 미리 큐에 넣어둡니다.
            frame = cam.get_frame()
            cam.queue_frame(frame)
            
            cam.start_streaming(frame_callback)
            print("Press enter to stop...")
            input()
            cam.stop_streaming()

if __name__ == '__main__':
    main()
