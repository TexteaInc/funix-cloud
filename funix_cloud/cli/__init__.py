import datetime
import json
import os
import tempfile
import time
import zipfile
from getpass import getpass
from pathlib import Path
from typing import Optional, TypedDict, Literal

import dateutil
import requests
from dateutil import parser
from qrcode import QRCode
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm, Prompt
from tzlocal import get_localzone

from funix_deploy.api import API, print_from_resp, Routes, ServerResponse, instance_stage_from_int, print_from_err, \
    ErrorCodes
from funix_deploy.config import ConfigDict
from funix_deploy.util import is_git_url, is_zip, zip_folder, check_username, check_password, check_email

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
    "query": "query",
    "list": "list",
    "restore": "restore",
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
            os.path.expanduser("~/.config/funix-cloud/config.json")
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

    def register(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        email: Optional[str] = None,
    ):
        """
        Register a new account on the Funix Cloud.
        """
        if username is None:
            while True:
                username = str(Prompt.ask("What is a user name you preferred")).lower()
                if check_username(username):
                    break
                self.__print_markdown("Usernames must be at least five characters long and "
                                      "can only contain numbers, letters, hyphen, and underscores.")

        if email is None:
            while True:
                email = Prompt.ask("What is your email")
                if check_email(email):
                    break
                self.__print_markdown("Your email seems not correct, please input again")

        if password is None:
            while True:
                password = Prompt.ask("Password", password=True)
                if not check_password(password):
                    password = None
                    print_from_err(self.__console, ErrorCodes.InvalidPassword)
                    continue

                password_confirm = Prompt.ask("Confirm Password", password=True)
                if password == password_confirm:
                    break
                self.__print_markdown("Your password does not match, please input again")

        register_resp = self.__api.register(username, password)
        if register_resp["code"] != 0:
            self.__print_markdown("Failed to register, please try again")
            print_from_resp(self.__console, register_resp)
            return

        login_resp = self.__api.login(username, password)
        if login_resp["code"] != 0:
            self.__print_markdown("Failed to login, please try again")
            print_from_resp(self.__console, register_resp)
            return

        self.__token = login_resp["data"]["token"]
        self.__config.set("token", login_resp["data"]["token"])
        self.__console.print("Login successful! Your token is saved.")

        self.__console.print("Sending verification email...")
        self.email(email)

    def deploy(
        self,
        url_or_path: str,
        instance_name: str,
        file: str = "main.py",
        no_frontend: bool = False,
        transform: bool = False,
        app_secret: str | None = None,
        rate_limiters: list[RateLimiter] | None = None,
        env: dict[str, str] | None = None,
    ):
        """
        Deploy local folder to Funix Cloud.

        Args:
            url_or_path (str): Git URL or local python path.
            instance_name (str): The name of new instance
            file (str, optional): The entry file to run. Defaults to "main.py".
            no_frontend (bool, optional): Whether to disable the frontend. Defaults to False.
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

            is_file = os.path.isfile(url_or_path)
            is_zipfile = is_zip(path) if is_file else False

            if is_zipfile:
                found = False
                with zipfile.ZipFile(path) as _zip:
                    for zf in _zip.filelist:
                        if zf.orig_filename == file:
                            found = True
                            break

                if not found:
                    self.__print_markdown(f"The entry file `{file}` is not in zip file `{path}`, "
                                          f"please specify it with `--file` option")
                    return

                print("Uploading deployment zip...")
                file_id = self.__upload(path)

            elif is_file and path.suffix == ".py":
                requirements_path = path.parent.joinpath("requirements.txt")
                if not requirements_path.exists():
                    create_requirements = Confirm.ask(
                        f"File `{requirements_path}` is not found... It's required for deployment.\n"
                        f"Do you want to create a `requirements.txt` that "
                        f"only contains the `funix` dependency and continue?")

                    if not create_requirements:
                        return

                    with open(requirements_path, "w") as f:
                        f.write("funix\n")

                with tempfile.NamedTemporaryFile(prefix="funix-cloud-", suffix=".zip") as tmp:
                    print("Compressing deployment zip...")
                    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as archive:
                        archive.writestr("main.py", path.read_text())
                        archive.writestr("requirements.txt", requirements_path.read_text())
                    print("Uploading deployment zip...")
                    file_id = self.__upload(tmp.name)

            elif os.path.isdir(path):
                entry_file: Path = Path(os.path.join(path, file))
                if not entry_file.exists():
                    self.__print_markdown(f"The entry file `{entry_file.absolute()}` is not exist, "
                                          f"please specify it with `--file` option")
                    return

                with tempfile.NamedTemporaryFile(prefix="funix-cloud-", suffix=".zip") as tmp:
                    print("Compressing deployment zip...")
                    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as archive:
                        zip_folder(path.absolute(), archive)
                    print("Uploading deployment zip...")
                    file_id = self.__upload(tmp.name)

            else:
                self.__print_markdown(f"File `{url_or_path}` is not a zip or a python file.")
                return

            if file_id is None:
                self.__print_markdown("Failed to upload deploy code")
                return

            req_json["file_id"] = file_id

        else:
            self.__print_markdown(f"Unexpected `{url_or_path}`, expected a URL or a local path.")
            return

        req_json.update({
            "name": instance_name,
            "entry_point": file,
            "with_no_frontend": no_frontend,
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

        print("Getting deploying status, press ^C or ^D to exit.")
        status = self.__console.status("Waiting for deploying...")
        status._live.transient = False
        with status:
            prev_errcode = None
            prev_stage = None
            prev_health = ""
            while True:
                info: ServerResponse = self.__api.query_instance(instance_id, self.__token)
                if info["code"] != 0:
                    print_from_resp(self.__console, info)
                    time.sleep(0.5)
                    continue

                data = info["data"]

                cur_stage = data["state"]
                cur_errcode = data["status"]

                first = prev_stage is None or prev_errcode is None
                updated = prev_stage != cur_stage or prev_errcode != cur_errcode
                if not (first or updated):
                    time.sleep(0.5)
                    continue

                if cur_errcode != 0:
                    status.update("Deployment failed")
                    status.stop()
                    print_from_err(self.__console, ErrorCodes(cur_errcode))
                    break

                if cur_stage == 200 and prev_health.lower() == "ok":
                    status.update("Deployment completed! You can now enjoy the funix cloud.")
                    status.stop()
                    self.query(instance_id)
                    break

                stage_str = instance_stage_from_int(cur_stage)
                if cur_stage != 200:
                    status.update(f"Deploying... Current Stage: {stage_str}")
                else:
                    resp: ServerResponse = self.__api.query_instance_health(instance_id, self.__token)
                    if resp["code"] != 0:
                        print_from_resp(self.__console, resp)
                        continue

                    data = resp["data"]
                    desc = "Unknown"
                    color = "Grey"
                    causes: list[str] = []
                    if data:
                        desc = data.get("desc") or desc
                        color = data.get("color") or color
                        causes = data.get("causes") or causes

                    # https://rich.readthedocs.io/en/stable/appendix/colors.html
                    match color:
                        case "Green":
                            color = "spring_green3"
                        case "Grey":
                            color = "grey58"
                        case "Yellow":
                            color = "bright_yellow"
                        case "Red":
                            color = "red3"
                        case _:
                            # unknown fallback
                            color = "grey58"

                    prev_health = desc
                    status_str = f"Waiting for initialization... Health: [{color}]{desc}[/]"

                    if len(causes) != 0:
                        status_str += "\nReason:\n"
                        for cause in causes:
                            status_str += f"    {cause}\n"

                    status.update(status_str)

                time.sleep(0.5)

    def __print_instance(self, user_name: str, data):
        url1 = f"{data['name']}-{user_name}.funix.io"
        url2 = f"funix.io/{user_name}/{data['name']}"
        markdown = f"- Name: {data['name']}\n" \
                   f"- ID: {data['id']}\n" \
                   f"- Domain: [{url1}](https://{url1}) or [{url2}](https://{url2})\n"

        start_time = data.get("start_time")
        if start_time:
            parsed_time: datetime = dateutil.parser.isoparse(start_time)
            zone = get_localzone()
            ctime = parsed_time.astimezone(zone).strftime("%Y-%m-%d %H:%M:%S")
            markdown += f"- Created Time: {ctime} {zone.key}\n"

        markdown += f"- Status: {instance_stage_from_int(data['state'])}\n" \
                    f"- Error Code: {data['status']}\n"

        self.__print_markdown(markdown)
        error = data["status"]
        if error and error != 0:
            print_from_err(self.__console, ErrorCodes(error))

    def query(self, instance_id: int, raw: bool = False):
        """
        Query an instance from Funix Cloud

        Args:
            instance_id(int): Instance id
            raw(bool): Print raw JSON response
        """
        info: ServerResponse = self.__api.query_instance(instance_id, self.__token)
        if info["code"] != 0:
            print_from_resp(self.__console, info)
            return

        me = self.__api.me(self.__token)
        if me["code"] != 0:
            print_from_resp(self.__console, me)
            return

        me_name = me["data"]["username"]
        data = info["data"]
        if raw:
            self.__print_json(data)
            return

        self.__print_instance(me_name, data)

    def restore(self, instance_id: int):
        """
        Restore an instance from Funix Cloud

        Args:
            instance_id(int): Instance id
        """
        info: ServerResponse = self.__api.restore_instance(instance_id, self.__token)

        if info["code"] != 0:
            print_from_resp(self.__console, info)
            return

        self.query(instance_id)

    def list(self):
        """
        List all instances of the current account
        """

        resp = self.__api.query_all_instance(self.__token)
        if resp["code"] != 0:
            print_from_resp(self.__console, resp)
            return

        instances: list = resp["data"]
        instances_len = len(instances)
        if instances_len == 0:
            print("No instances created")
            return

        me = self.__api.me(self.__token)
        if me["code"] != 0:
            print_from_resp(self.__console, me)
            return

        me_name = me["data"]["username"]

        self.__print_markdown(f"There are total {instances_len} instances:")
        self.__print_markdown("----")

        for instance in instances:
            self.__print_instance(me_name, instance)
            self.__print_markdown("----")

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
                f"Password changed successful! Funix-cloud will log you out soon, "
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
