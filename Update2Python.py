import subprocess
import pkg_resources
import time

start = time.time()

packages = [dist.project_name for dist in pkg_resources.working_set]
for package in packages:
    subprocess.call(f"pip install --upgrade {package}", shell=True)

python_version =  subprocess.call("python --version", shell=True)

end = time.time()
spend_time = end - start

print()
print("User Python Version: ", python_version)
print("Update Time: ", spend_time)
print("Packages Updated Complete")

# for update pip
# C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe -m pip install --upgrade pip