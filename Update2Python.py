import subprocess
import pkg_resources
import time
import tkinter as tk
from tkinter import ttk

start = time.time()

packages = [dist.project_name for dist in pkg_resources.working_set]

for package in packages:
    try:
        subprocess.run(
            ["pip", "install", "--upgrade", package],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to upgrade {package}: {e}")

try:
    python_version = subprocess.check_output(["python", "--version"], stderr=subprocess.DEVNULL).decode().strip()
except subprocess.CalledProcessError:
    python_version = "Unknown"

end = time.time()
spend_time = end - start

print()
print("User Python Version: ", python_version)
print("Update Time: ", spend_time)
print("Packages Updated Complete")

