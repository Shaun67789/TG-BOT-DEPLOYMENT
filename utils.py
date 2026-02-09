import os
import zipfile
import shutil

def safe_extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_to)

    # Flatten if zip has single root folder
    files = os.listdir(extract_to)
    if len(files) == 1:
        root = os.path.join(extract_to, files[0])
        if os.path.isdir(root):
            for item in os.listdir(root):
                shutil.move(os.path.join(root, item), extract_to)
            shutil.rmtree(root)
