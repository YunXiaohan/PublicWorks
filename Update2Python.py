import subprocess
import pkg_resources

packages = [dist.project_name for dist in pkg_resources.working_set]
for package in packages:
    subprocess.call(f"pip install --upgrade {package}", shell=True)

python_version =  subprocess.call("python --version", shell=True)

print()
print("User Python Version: ", python_version)
print("Packages Updated Complete")
