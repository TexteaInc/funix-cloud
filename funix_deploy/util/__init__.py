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


def zip_folder(path, zip_handler: zipfile.ZipFile):
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


def is_zip(path) -> bool:
    with open(path, "rb") as f:
        head: bytes = f.read(4)
        return head == b"PK\x03\x04" or head == b"PK\x05\x06" or head == b"PK\x07\x08"


def check_username(name: str) -> bool:
    if len(name) < 5 or len(name) > 50:
        return False

    for ch in name:
        valid = ch.isalnum() or ch == '_' or ch == '-'
        if not valid:
            return False

    return True


def check_email(email: str) -> bool:
    if '@' not in email:
        return False

    return True


__pwd_special_chars = "!@#$%^&*()_+-=,.<>?;:[]{}|~"


def check_password(pwd: str) -> bool:
    if len(pwd) < 8 or len(pwd) > 64:
        return False

    has_upper = False
    has_lower = False
    has_number = False
    has_special = False
    for ch in pwd:
        if not ch.isascii():
            return False
        valid = ch.isalnum() or ch in __pwd_special_chars
        if not valid:
            return False
        if ch.isupper():
            has_upper = True
        if ch.islower():
            has_lower = True
        if ch.isnumeric():
            has_number = True
        if ch in __pwd_special_chars:
            has_special = True

    if int(has_upper) + int(has_lower) + int(has_number) + int(has_special) < 2:
        return False

    return True
