import json
import os
import tempfile
import zipfile
from getpass import getpass
from pathlib import Path
from typing import Optional, TypedDict, Literal

import requests
from qrcode import QRCode
from rich.console import Console
from rich.markdown import Markdown

from funix_deploy.api import API, print_from_resp, Routes, ServerResponse
from funix_deploy.config import ConfigDict
from funix_deploy.util import is_git_url

maps = {
    "register": "register",
    "login": "login",
    "logout": "logout",
    "email": "email",
    "me": "me",
    "2fa": "two_fa",
    "change-password": "change_password",
    "forget-password": "forget_password",
    "deploy": "deploy",
    "delete": "delete",
    "remove": "delete",
}


class RateLimiter(TypedDict):
    max_calls: int
    period: int
    source: Literal["browser", "ip"]


class DeployCLI:
    """
    Funix Deploy CLI.

    You can use this to deploy your projects to the Funix Cloud.
    """

    def __getattribute__(self, item):
        if item in maps:
            return super(DeployCLI, self).__getattribute__(maps[item])
        else:
            return super(DeployCLI, self).__getattribute__(item)

    def __dir__(self):
        return list(maps.keys())

    def __init__(self):
        self.__config = ConfigDict(
            os.path.expanduser("~/.config/funix-deploy/config.json")
        )
        self.__console = Console()
        self.__api = API(self.__config.get("api_server", "https://cloud-dev.funix.io"))
        self.__token = self.__config.get("token", None)

    def __print_json(self, data: dict):
        self.__console.print_json(
            json.dumps(data, ensure_ascii=False),
            indent=2,
            highlight=True,
            sort_keys=True,
            ensure_ascii=False,
        )

    def __print_markdown(self, data: str):
        self.__console.print(Markdown(data))

    def __upload(self, path) -> Optional[str]:
        resp: ServerResponse = self.__api.upload(path, self.__token)
        if resp["code"] != 0:
            print_from_resp(self.__console, resp)
            return
        return resp["data"]["file_id"]

    def register(self, username: str, email: Optional[str] = None):
        """
        Register a new account on the Funix Cloud.

        Args:
            username (str): Username to register with.
            email (Optional[str], optional): Email to bind with. Defaults to None.
        """
        password = getpass("Please input password: ")
        confirm_password = getpass("Please confirm password: ")
        if password != confirm_password:
            self.__console.print("Passwords don't match.")
            return

        result = self.__api.register(username, password)

        if result["code"] == 0:
            self.__console.print("Register successful! Log in now.")
            token = self.__api.login(username, password)["data"]["token"]
            self.__config.set("token", token)
            self.__token = token
            self.__console.print("Login successful! Your token is saved.")
        else:
            print_from_resp(self.__console, result)
            return

        if email:
            self.email(email)

    def deploy(
            self,
            url_or_path: str,
            instance_name: str,
            file: str = "main.py",
            no_frontend: bool = False,
            lazy: bool = False,
            dir_mode: bool = False,
            transform: bool = False,
            app_secret: str | None = None,
            rate_limiters: list[RateLimiter] = [],
            env: dict[str, str] = {},
    ):
        """
        Deploy local folder to Funix Cloud.

        Args:
            url_or_path (str): Git URL or local python path.
            instance_name (str): The name of new instance
            file (str, optional): The entry file to run. Defaults to "main.py".
            no_frontend (bool, optional): Whether to disable the frontend. Defaults to False.
            lazy (bool, optional): Whether to use lazy mode. Defaults to False.
            dir_mode (bool, optional): Whether to use directory mode. Defaults to False.
            transform (bool, optional): Whether to use transform mode. Defaults to False.
            app_secret (str | None, optional): The app secret. Defaults to None.
            rate_limiters (list[RateLimiter], optional): The rate limiters. Defaults to [].
                Example: "[{'max_calls': 10, 'period': 60, 'source': 'browser'}]"
            env (dict[str, str], optional): The environment variables. Defaults to []. Example: "{'key': 'value'}"
        """

        req_json = {}

        if is_git_url(url_or_path):
            url = self.__api.base_url + Routes.deploy_git
            git = url_or_path
            req_json["repo_link"] = git

        elif os.path.exists(url_or_path):
            url = self.__api.base_url + Routes.deploy_zip
            path: Path = Path(url_or_path)

            if not os.path.isfile(url_or_path):
                self.__print_markdown(
                    f"File `{url_or_path}` is not a file... Currently, directory is not supported yet.")
                return

            with open(path, "rb") as f:
                head: bytes = f.read(4)
                is_zip = head == b"PK\x03\x04" or head == b"PK\x05\x06" or head == b"PK\x07\x08"

            if is_zip:
                file_id = self.__upload(path.name)
                if file_id is None:
                    return
            elif path.suffix == ".py":
                requirements_path = path.parent.joinpath("requirements.txt")
                if not requirements_path.exists():
                    self.__print_markdown(
                        f"File `{requirements_path}` is not found... A `requirements.txt` is required for deployment.")
                    return

                with tempfile.NamedTemporaryFile(prefix="funix-deploy-", suffix=".zip") as tmp:
                    print("Compressing deployment zip...")
                    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as archive:
                        archive.writestr("main.py", path.read_text())
                        archive.writestr("requirements.txt", requirements_path.read_text())
                    print("Uploading deployment zip...")
                    file_id = self.__upload(tmp.name)
                    if file_id is None:
                        return

            else:
                self.__print_markdown(f"File `{url_or_path}` is not a zip or a python file.")
                return

            if file_id is None:
                self.__print_markdown(
                    "Illegal state, something wrong, file_id is None, please contact developer to fix this.")
                return

            req_json["file_id"] = file_id

        else:
            self.__print_markdown(f"Unexpected `{url_or_path}`, expected a URL or a local path.")
            return

        req_json.update({
            "name": instance_name,
            "entry_point": file,
            "with_no_frontend": no_frontend,
            "with_lazy": lazy,
            "with_dir_mode": dir_mode,
            "with_transform": transform,
        })

        if app_secret and isinstance(app_secret, str):
            req_json["app_secret"] = app_secret

        if rate_limiters and isinstance(rate_limiters, list):
            req_json["rate_limiters"] = rate_limiters

        if env and isinstance(env, dict):
            req_json["envs"] = env

        r = requests.post(
            url,
            json=req_json,
            headers={"Authorization": f"Bearer {self.__token}"},
        )

        result: ServerResponse = r.json()

        if result["code"] != 0:
            print("Failed to deploy!")
            print_from_resp(self.__console, result)
            return

        app_name = result["data"]["application_name"]
        instance_id = result["data"]["instance_id"]
        self.__print_markdown(
            "Successfully created deployment task!\n"
            f"- App name: {app_name}\n"
            f"- Instance id: {instance_id}\n"
        )

    def delete(self, instance_id: int):
        """
        Delete an instance from Funix Cloud

        Args:
            instance_id(int): Instance id
        """

        result: ServerResponse = self.__api.remove_instance(instance_id, self.__token)
        if result["code"] != 0:
            print_from_resp(self.__console, result)
            return

        self.__print_markdown(f"Successfully removed instance `{instance_id}`!")

    def login(self, username: str):
        """
        Login to the Funix Cloud.

        Args:
            username (str): Username to log in with.
        """
        password = getpass("Please input password: ")
        result = self.__api.login(username, password)

        if result["code"] == 0:
            self.__token = result["data"]["token"]
            self.__config.set("token", result["data"]["token"])
            self.__console.print("Login successful! Your token is saved.")
        else:
            print_from_resp(self.__console, result)

    def logout(self):
        """
        Logout from the Funix Cloud.
        """
        self.__token = None
        self.__config.set("token", None)
        self.__console.print("Logout successful!")

    def email(self, email: str):
        """
        Bind an email to your account.

        Args:
            email (str): Email to bind.
        """
        if not self.__token:
            self.__console.print("Please login first.")
            return

        if "@" not in email:
            self.__print_markdown("Your email does not seem correct, please check and try again.")
            return

        result = self.__api.bind_email(self.__token, email)

        if result["code"] == 0:
            self.__print_markdown(
                f"Your email `{email}` will receive a verification link, please check your inbox."
            )
        else:
            print_from_resp(self.__console, result)

    def me(self):
        """
        Get your account profile.
        """
        if not self.__token:
            self.__console.print("Please login first.")
            return

        result = self.__api.me(self.__token)

        if result["code"] == 0:
            me_data = result["data"]
            list_str = f"- ID: {me_data['id']}\n"
            list_str += f"- Username: {me_data['username']}\n"
            if "email" in me_data:
                if email := me_data["email"]:
                    list_str += f"- Email: {email}\n"
                else:
                    list_str += "- Email: Not bound\n"
            else:
                list_str += "- Email: Not bound\n"
            if me_data["has_2fa"]:
                list_str += "- 2FA: Bound"
            else:
                list_str += "- 2FA: Not bound"
            self.__print_markdown(list_str)
        else:
            print_from_resp(self.__console, result)

    def two_fa(self):
        """
        Bind 2FA
        """
        if not self.__token:
            self.__console.print("Please login first.")
            return

        generate_result = self.__api.two_fa_request(self.__token)

        if generate_result["code"] != 0:
            print_from_resp(
                self.__console, generate_result
            )
            return

        ticket = generate_result["data"]["ticket"]
        otpauth: str = generate_result["data"]["otpauth"]
        qr = QRCode()
        qr.add_data(otpauth)

        secret = otpauth.split("secret=")[1].split("&")[0]

        qr.print_ascii()
        self.__print_markdown(
            f"If you cannot scan QR Code, please input secret code in your 2FA app by yourself: "
            f"`{secret}`"
        )
        code = input("Please input the code from your 2FA app: ")

        result = self.__api.two_fa_bind(self.__token, ticket, code)

        if result["code"] == 0:
            self.__print_markdown(f"2FA bind successful!")
        else:
            print_from_resp(self.__console, result)

    def change_password(self):
        """
        Change password your password.
        """
        if not self.__token:
            self.__console.print("Please login first.")
            return

        old_password = getpass("Please input old password: ")
        new_password = getpass("Please input new password: ")
        if old_password == new_password:
            self.__console.print("New password cannot be the same as old password.")
            return
        confirm_password = getpass("Please confirm new password: ")
        if new_password != confirm_password:
            self.__console.print("Passwords don't match.")
            return

        result = self.__api.change_password(self.__token, old_password, new_password)

        if result["code"] == 0:
            self.__print_markdown(
                f"Password changed successful! Funix-deploy will log you out soon, "
                f"you need log in again."
            )
            self.logout()
        else:
            print_from_resp(self.__console, result)

    def forget_password(self, username: str, email: str):
        """
        If you forget your password, you can use this to reset your password.

        Args:
            username (str): Username to reset password.
            email (str): Email to reset password.
        """

        result = self.__api.forget_password(username, email)
        if result["code"] == 0:
            self.__print_markdown(f"Please check your email `{email}` for code.")
        else:
            print_from_resp(self.__console, result)

        ticket = result["data"]["ticket"]
        code = int(input("Please input the code from your email: "))
        new_password = getpass("Please input new password: ")
        confirm_password = getpass("Please confirm new password: ")

        if new_password != confirm_password:
            self.__console.print("Passwords don't match.")
            return

        result = self.__api.reset_password(ticket, code, new_password)
        if result["code"] == 0:
            self.__print_markdown(f"Password reset successful!")
        else:
            print_from_resp(self.__console, result)
