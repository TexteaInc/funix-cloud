import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, TypedDict

import requests
from rich.console import Console
from rich.markdown import Markdown


class ServerResponse(TypedDict):
    code: int
    message: str
    data: Optional[Any]


class ErrorCodes(Enum):
    Success = 0
    ServerError = 500
    DatabaseError = 501
    InvalidArguments = 510
    NoAccessPermission = 511
    # Account Error Code
    InvalidUsername = 100001
    InvalidPassword = 100002
    SamePassword = 100003
    UsernameAlreadyExists = 100004
    IncorrectPassword = 100005
    MismatchedEmail = 100006
    EmailSendTooFrequently = 100007
    RequireEmailVerification = 100008
    InvalidBindingTicket = 100009
    InvalidBindingCode = 100010
    AlreadyHas2FA = 100011
    # Instance Error Code
    CannotCloneGitRepo = 103001
    SpecialFoldersNotAllowed = 103002
    GitFolderNotAllowed = 103003
    RequirementsTxtNotFound = 103004
    NoFunixInRequirementsTxt = 103005
    FileTooLarge = 103006
    FileNotFound = 103007
    IllegalString = 103008
    ArgumentTooLong = 103009
    InstancesTooMany = 103013
    DuplicationName = 103014
    InstanceNotFound = 103016
    UserHasNoInstance = 103018
    InstanceNotPrepared = 103019
    BodyNoMultiPart = 103020
    FileIsCleaned = 103021
    InstanceNotPaused = 103022


def instance_stage_from_int(code: int):
    match code:
        case 100:
            return "Start"
        case 101:
            return "Preprocess"
        case 102:
            return "Prepare"
        case 103:
            return "Upload"
        case 104:
            return "Deploying"
        case 200:
            return "Success"
        case 201:
            return "Paused"
        case 400:
            return "Failed"
        case _:
            return f"Unknown {code}"


def __print_json(console: Console, data: dict | None):
    if data is None:
        return

    console.print_json(
        json.dumps(data, ensure_ascii=False),
        indent=2,
        highlight=True,
        sort_keys=True,
        ensure_ascii=False,
    )


def __print_markdown(console, data: str):
    console.print(Markdown(data))


def print_from_resp(
        console: Console,
        response: ServerResponse,
):
    code = ErrorCodes(response["code"])
    print_from_err(console, code, response)


def print_from_err(console: Console, code: ErrorCodes, data: dict | None = None):
    match code:
        case ErrorCodes.Success:
            return
        case ErrorCodes.ServerError:
            __print_markdown(
                console,
                "Oops! The funix cloud server seems having some problems now, your request cannot be processed. "
                "Here is the raw response if you want to report a new issue:"
            )
            __print_markdown(console, "\n----\n")
            __print_json(console, data)
        case ErrorCodes.DatabaseError:
            __print_markdown(
                console,
                "Database error. Please read the raw message below and check if your actions are correct. "
                "If you are sure your actions are correct, please report a new issue."
            )
            __print_markdown(console, "\n----\n")
            __print_json(console, data)
        case ErrorCodes.InvalidArguments:
            __print_markdown(
                console,
                "Invalid arguments. Please check your arguments. "
                "If everything is correct with your arguments, "
                "it could be a problem caused by kumo or funix-cloud not being updated in time, "
                "you can either report a new issue or wait for an update."
            )
            __print_markdown(console, "\n----\n")
            __print_json(console, data)
        case ErrorCodes.NoAccessPermission:
            __print_markdown(
                console,
                "No access permission. You may need to log in, "
                "or you may have accidentally entered an incorrect user/instance ID. "
                "Below is the raw message, if everything is fine but the error just happens, please report a new issue."
            )
            __print_markdown(console, "\n----\n")
            __print_json(console, data)
        case ErrorCodes.InvalidUsername:
            __print_markdown(
                console,
                "Invalid username. Username length should be 5-50, and only contains letters, numbers, "
                "underscores and hyphens."
            )
        case ErrorCodes.InvalidPassword:
            __print_markdown(
                console,
                "Invalid password. Password length should be 8-64, "
                "and it should contain at least two of following: \n"
                "- Uppercase letters\n"
                "- Lowercase letters\n"
                "- Numbers\n"
                "- Special characters\n"
            )
        case ErrorCodes.SamePassword:
            __print_markdown(
                console,
                "Same password. The password cannot be the same as the one you are currently using. "
                "Maybe it reminds you of your password, haha."
            )
        case ErrorCodes.UsernameAlreadyExists:
            __print_markdown(
                console,
                "Someone else has the same idea as you. Your username is taken. But don't worry, "
                "Think a little bit, you can always come up with a better username."
            )
        case ErrorCodes.IncorrectPassword:
            __print_markdown(
                console,
                "Incorrect password. You may have entered the wrong password, if you don't remember your password, "
                "Use `funix-cloud reset-password` to reset your password."
            )
        case ErrorCodes.MismatchedEmail:
            __print_markdown(
                console,
                "You have entered the wrong email address, think about your email again, "
                "if you can't find it please contact support@funix.io"
            )
        case ErrorCodes.EmailSendTooFrequently:
            __print_markdown(
                console,
                "Take your time. You're really going too fast. Take a break. If you don't get the email, "
                "contact support@funix.io"
            )
            __print_json(console, data)
        case ErrorCodes.RequireEmailVerification:
            __print_markdown(
                console,
                "You need to verify your email address before you can perform this operation. "
                "Use `funix-cloud email [your_email]` to bind your email address."
            )
        case ErrorCodes.InvalidBindingTicket:
            __print_markdown(
                console,
                "Invalid binding ticket. You may have entered the wrong ticket, check it again."
            )
        case ErrorCodes.InvalidBindingCode:
            __print_markdown(
                console,
                "Invalid binding code. You may have entered the wrong code, check it again."
            )
        case ErrorCodes.AlreadyHas2FA:
            __print_markdown(console, "You have already has 2fa, don't need to bind again.")
        case ErrorCodes.CannotCloneGitRepo:
            __print_markdown(
                console,
                "Funix cloud cannot clone your git repo. Please check your repo url, if it's private, "
                "please make it public or upload it in zip file."
            )
        case ErrorCodes.SpecialFoldersNotAllowed:
            __print_markdown(
                console,
                "Please delete `.ebextensions` and `.platform` in your project."
            )
        case ErrorCodes.GitFolderNotAllowed:
            __print_markdown(console, "Please delete `.git` folder in your project.")
        case ErrorCodes.RequirementsTxtNotFound:
            __print_markdown(
                console,
                "You need `requirements.txt` in your project, if you don't have, "
                "please create one, make sure it contains `funix`."
            )
        case ErrorCodes.NoFunixInRequirementsTxt:
            __print_markdown(
                console,
                "You need `funix` in your `requirements.txt`, please add it."
            )
        case ErrorCodes.FileTooLarge:
            __print_markdown(
                console,
                "File too large. Please make sure your file is less than 200MB. If you need to upload a larger file, "
                "you can use AWS or Google Cloud, or contact support@funix.io."
            )
        case ErrorCodes.FileNotFound:
            __print_markdown(
                console,
                "Your python main file is not found. Please make sure your file exists and you have the correct path."
            )
        case ErrorCodes.IllegalString:
            __print_markdown(
                console,
                "Your argument contains illegal characters, remove: _()[]<>:\"'/\\|?*"
            )
        case ErrorCodes.ArgumentTooLong:
            __print_markdown(
                console,
                "Your argument is too long, more than 128 characters. Please shorten it."
            )
        case ErrorCodes.InstancesTooMany:
            __print_markdown(
                console,
                "You already have 10 instances in your account, if you need more, please contact support@funix.io"
            )
        case ErrorCodes.DuplicationName:
            __print_markdown(
                console,
                "You have already used this app name, you can delete the previous instance or use another one."
            )
        case ErrorCodes.InstanceNotFound:
            __print_markdown(console, "Instance not found, please check your instance id.")
        case ErrorCodes.UserHasNoInstance:
            __print_markdown(console, "You have no instance, but you can create one if you want.")
        case ErrorCodes.InstanceNotPrepared:
            __print_markdown(
                console,
                "Please wait for the instance to be prepared, try again later. "
                "If your instance is still not ready after a long time, please contact support@funix.io"
            )
        case ErrorCodes.BodyNoMultiPart:
            __print_markdown(
                console,
                "It seems like you didn't upload any files, please check your request."
            )
        case ErrorCodes.FileIsCleaned:
            __print_markdown(
                console,
                "The file could not be found or was removed because of the 30-minute temporary file limit. "
                "Please check your file_id and upload again if it was removed due to a timeout."
            )
        case ErrorCodes.InstanceNotPaused:
            __print_markdown(console, "Your instance is not paused, you cannot restore it.")
        case _:
            __print_markdown(console, f"Unknown error code `{code}`.")
            return


@dataclass
class Routes:
    login: str = "/user/login"
    register: str = "/user/register"
    email: str = "/user/email/bind"
    me: str = "/user/me"
    two_fa_request: str = "/user/2fa/generate"
    two_fa_bind: str = "/user/2fa/bind"
    change_password: str = "/user/password/change"
    forget_password: str = "/user/password/forget"
    reset_password: str = "/user/password/reset"
    upload: str = "/file/upload"
    remove_instance: str = "/instance/remove"
    deploy_git: str = "/instance/create/git"
    deploy_zip: str = "/instance/create/upload"
    query_instance: str = "/instance/query"
    query_instance_health: str = "/instance/health"
    query_all_instance: str = "/instance/query/all"
    restore_instance: str = "/instance/restore"


class API:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def login(self, username: str, password: str) -> ServerResponse:
        r = requests.post(
            self.base_url + Routes.login,
            json={"username": username, "password": password},
        )
        return r.json()

    def register(self, username: str, password: str) -> ServerResponse:
        r = requests.post(
            self.base_url + Routes.register,
            json={"username": username, "password": password},
        )
        return r.json()

    def bind_email(self, token: str, email: str) -> ServerResponse:
        r = requests.post(
            self.base_url + Routes.email,
            json={"email": email},
            headers={"Authorization": f"Bearer {token}"},
        )
        return r.json()

    def me(self, token: str) -> ServerResponse:
        r = requests.post(
            self.base_url + Routes.me,
            headers={"Authorization": f"Bearer {token}"},
        )
        return r.json()

    def two_fa_request(self, token: str) -> ServerResponse:
        r = requests.post(
            self.base_url + Routes.two_fa_request,
            headers={"Authorization": f"Bearer {token}"},
        )
        return r.json()

    def two_fa_bind(self, token: str, ticket: str, code: str) -> ServerResponse:
        r = requests.post(
            self.base_url + Routes.two_fa_bind,
            json={"ticket": ticket, "code": code},
            headers={"Authorization": f"Bearer {token}"},
        )
        return r.json()

    def change_password(
            self, token: str, old_password: str, new_password: str
    ) -> ServerResponse:
        r = requests.post(
            self.base_url + Routes.change_password,
            json={"old_password": old_password, "new_password": new_password},
            headers={"Authorization": f"Bearer {token}"},
        )
        return r.json()

    def forget_password(self, username: str, email: str):
        r = requests.post(
            self.base_url + Routes.forget_password,
            json={"username": username, "email": email},
        )
        return r.json()

    def reset_password(self, ticket: str, code: int, password: str):
        r = requests.post(
            self.base_url + Routes.reset_password,
            json={"ticket": ticket, "code": code, "password": password},
        )
        return r.json()

    def upload(self, path: str, token: str):
        r = requests.post(
            self.base_url + Routes.upload,
            files={"file": ("deploy.zip", open(path, "rb"))},
            headers={"Authorization": f"Bearer {token}"},
        )
        return r.json()

    def remove_instance(self, instance_id: int, token: str):
        r = requests.post(
            self.base_url + Routes.remove_instance,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "id": instance_id,
            }
        )
        return r.json()

    def query_instance(self, instance_id: int, token: str):
        r = requests.post(
            self.base_url + Routes.query_instance,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "id": instance_id,
            }
        )
        return r.json()

    def restore_instance(self, instance_id: int, token: str):
        r = requests.post(
            self.base_url + Routes.restore_instance,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "id": instance_id,
            }
        )
        return r.json()

    def query_instance_health(self, instance_id: int, token: str):
        r = requests.post(
            self.base_url + Routes.query_instance_health,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "id": instance_id,
            }
        )
        return r.json()

    def query_all_instance(self, token: str):
        r = requests.post(
            self.base_url + Routes.query_all_instance,
            headers={"Authorization": f"Bearer {token}"},
        )
        return r.json()
