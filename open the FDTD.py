import numpy as np
import matplotlib.pyplot as plt
import os
import importlib.util
import sys

# Define the module name and file path
module_name = "lumapi"
file_path = "C:\\Program Files\\Lumerical\\v241\\api\\python\\lumapi.py"

# Add the DLL directory to the PATH
os.add_dll_directory("C:\\Program Files\\Lumerical\\v241\\api\\python")

# Check if the file path exists
if not os.path.exists(file_path):
    print(f"Error: The specified file path {file_path} does not exist.")
else:
    # Load the lumapi module using importlib
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    lumapi = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = lumapi
    spec.loader.exec_module(lumapi)

    # Now you can use the FDTD class from the lumapi module
    fdtd = lumapi.FDTD()

    # Example usage: (customize this part based on your specific needs)
    fdtd.addfdtd(x=0, y=0, z=0,x_span=1e-6, y_span=1e-6, z_span=3e-6)
    fdtd.addrect(x=0, y=0, z=0, x_span=0.5e-6, y_span=0.5e-6, z_span=1e-6)
    fdtd.addplane(x=0, y=0, z=-1e-6, x_span=2e-6, y_span=2e-6)
    fdtd.addpower(x=0, y=0, z=-1.5e-6, x_span=2e-6, y_span=2e-6)
    fdtd.save("open_py")
    fdtd.run()