import io
import json
import os
from getpass import getpass
from typing import Optional

from qrcode import QRCode
from rich.console import Console
from rich.markdown import Markdown

from funix_deploy.api import API, print_markdown_from_full_error_server_response
from funix_deploy.config import ConfigDict


maps = {
    "register": "register",
    "login": "login",
    "logout": "logout",
    "email": "email",
    "me": "me",
    "2fa": "two_fa",
    "change-password": "change_password",
    "forget-password": "forget_password",
}


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
            print_markdown_from_full_error_server_response(self.__console, result)
            return

        self.email(email)

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
            print_markdown_from_full_error_server_response(self.__console, result)

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

        result = self.__api.bind_email(self.__token, email)

        if result["code"] == 0:
            self.__print_markdown(
                f"Your email `{email}` will receive a verification link, please check your inbox."
            )
        else:
            print_markdown_from_full_error_server_response(self.__console, result)

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
            print_markdown_from_full_error_server_response(self.__console, result)

    def two_fa(self):
        """
        Bind 2FA
        """
        if not self.__token:
            self.__console.print("Please login first.")
            return

        generate_result = self.__api.two_fa_request(self.__token)

        if generate_result["code"] != 0:
            print_markdown_from_full_error_server_response(
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
            print_markdown_from_full_error_server_response(self.__console, result)

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
            print_markdown_from_full_error_server_response(self.__console, result)

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
            print_markdown_from_full_error_server_response(self.__console, result)

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
            print_markdown_from_full_error_server_response(self.__console, result)
