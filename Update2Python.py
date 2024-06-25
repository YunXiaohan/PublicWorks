import subprocess
import pkg_resources

subprocess.call("python --version", shell=True)

packages = [dist.project_name for dist in pkg_resources.working_set]
for package in packages:
    subprocess.call(f"pip install --upgrade {package}", shell=True)

