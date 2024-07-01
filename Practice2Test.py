
import os
import importlib.util
import sys

module_lumapi = "lumapi"
file_path = "C:\\Program Files\\Lumerical\\v241\\api\\python\\lumapi.py" # 라이브러리 경로
os.add_dll_directory("C:\\Program Files\\Lumerical\\v241\\api\\python") # 로컬 파이썬 경로

spec = importlib.util.spec_from_file_location(module_lumapi, file_path)
lumapi = importlib.util.module_from_spec(spec)
sys.modules[module_lumapi] = lumapi
spec.loader.exec_module(lumapi)

# 설계는 여기서
fdtd = lumapi.FDTD()

fdtd.addfdtd(x=0, y=0, z=0,x_span=1e-6, y_span=1e-6, z_span=3e-6)
fdtd.addrect(x=0, y=0, z=0, x_span=0.5e-6, y_span=0.5e-6, z_span=1e-6)
fdtd.addplane(x=0, y=0, z=-1e-6, x_span=2e-6, y_span=2e-6)
fdtd.addpower(x=0, y=0, z=-1.5e-6, x_span=2e-6, y_span=2e-6)
fdtd.save("open_py")
fdtd.run()

# 무한루프, 이거 필요없을지도
while True:
    command = input("Enter 'exit' to quit: ")
    if command.lower() == 'exit':
        break