import os
import zipfile


def is_git_url(s: str | None) -> bool:
    if s is None:
        return False

    # ad hoc check
    if "github.com" in s:
        return True

    if s.startswith("https://") and s.endswith(".git"):
        return True

    if s.startswith("git@") and s.endswith(".git"):
        return True

    return False


def zip_folder(path: str, zip_handler: zipfile.ZipFile):
    for folder_name, sub_folders, filenames in os.walk(path):
        for filename in filenames:
            if filename in ["deploy.zip", ".DS_Store", ".gitignore"]:
                continue
            if filename.endswith(".pyc"):
                continue
            if folder_name in ["__pycache__", ".git", ".ebextensions"]:
                continue
            file_path = os.path.join(folder_name, filename)
            zip_handler.write(file_path, arcname=os.path.relpath(file_path, path))
