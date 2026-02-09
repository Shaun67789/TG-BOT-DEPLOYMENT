import os
import zipfile
import shutil
import threading
import subprocess

def safe_extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_to)

    files = os.listdir(extract_to)
    if len(files) == 1:
        root = os.path.join(extract_to, files[0])
        if os.path.isdir(root):
            for item in os.listdir(root):
                shutil.move(os.path.join(root, item), extract_to)
            shutil.rmtree(root)

def install_requirements_async(bot_path, log_file):
    def run():
        req = os.path.join(bot_path, "requirements.txt")
        if not os.path.exists(req):
            return

        with open(log_file, "a") as f:
            f.write("📦 Installing requirements...\n")
            subprocess.call(
                ["pip", "install", "-r", "requirements.txt"],
                cwd=bot_path,
                stdout=f,
                stderr=f
            )
            f.write("✅ Requirements installed\n")

    threading.Thread(target=run, daemon=True).start()
