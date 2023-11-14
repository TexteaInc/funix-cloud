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


def print_from_resp(
    console: Console,
    response: ServerResponse,
):
    def print_json(data: dict):
        console.print_json(
            json.dumps(data, ensure_ascii=False),
            indent=2,
            highlight=True,
            sort_keys=True,
            ensure_ascii=False,
        )

    def print_markdown(data: str):
        console.print(Markdown(data))

    code=ErrorCodes(response["code"])

    match code:
        case ErrorCodes.Success:
            return
        case ErrorCodes.ServerError:
            print_markdown(
                "Oops! The funix cloud server seems having some problems now, your request cannot be processed. "
                "Here is the raw response if you want to report a new issue:\n----\n"
            )
            print_json(response)
        case ErrorCodes.DatabaseError:
            print_markdown(
                "Database error. Please read the raw message below and check if your actions are correct. "
                "If you are sure your actions are correct, please report a new issue.\n----\n"
            )
            print_json(response)
        case ErrorCodes.InvalidArguments:
            print_markdown(
                "Invalid arguments. Please check your arguments. "
                "If everything is correct with your arguments, "
                "it could be a problem caused by kumo or funix-deploy not being updated in time, "
                "you can either report a new issue or wait for an update.\n----\n"
            )
            print_json(response)
        case ErrorCodes.NoAccessPermission:
            print_markdown(
                "No access permission. You may need to log in, "
                "or you may have accidentally entered an incorrect user/instance ID or "
                "you may be planning a theft of some rainwater from our cloud servers. "
                "Below is the raw message, "
                "if everything is fine but the error just happens, please report a new issue.\n----\n"
            )
            print_json(response)
        case ErrorCodes.InvalidUsername:
            print_markdown(
                "Invalid username. Username length should be 5-50, and only contains letters, numbers, "
                "underscores and hyphens."
            )
        case ErrorCodes.InvalidPassword:
            print_markdown(
                "Invalid password. Password length should be 8-64, "
                "and it should contain at least two of following: \n"
                "- Uppercase letters"
                "- Lowercase letters"
                "- Numbers"
                "- Special characters"
            )
        case ErrorCodes.SamePassword:
            print_markdown(
                "Same password. The password cannot be the same as the one you are currently using. "
                "Maybe it reminds you of your password, haha."
            )
        case ErrorCodes.UsernameAlreadyExists:
            print_markdown(
                "Someone else has the same idea as you. Your username is taken. But don't worry, "
                "Think a little bit, you can always come up with a better username."
            )
        case ErrorCodes.IncorrectPassword:
            print_markdown(
                "Incorrect password. You may have entered the wrong password, if you don't remember your password, "
                "Use `funix-deploy reset-password` to reset your password."
            )
        case ErrorCodes.MismatchedEmail:
            print_markdown(
                "You have entered the wrong email address, think about your email again, "
                "if you can't find it please contact support@funix.io"
            )
        case ErrorCodes.EmailSendTooFrequently:
            print_markdown(
                "Take your time. You're really going too fast. Take a break. If you don't get the email, "
                "contact support@funix.io"
            )
            print_json(response)
        case ErrorCodes.RequireEmailVerification:
            print_markdown(
                "You need to verify your email address before you can perform this operation. "
                "Use `funix-deploy email [your_email]` to bind your email address."
            )
        case ErrorCodes.InvalidBindingTicket:
            print_markdown(
                "Invalid binding ticket. You may have entered the wrong ticket, check it again."
            )
        case ErrorCodes.InvalidBindingCode:
            print_markdown(
                "Invalid binding code. You may have entered the wrong code, check it again."
            )
        case ErrorCodes.AlreadyHas2FA:
            print_markdown("You have already has 2fa, don't need to bind again.")
        case ErrorCodes.CannotCloneGitRepo:
            print_markdown(
                "Funix cloud cannot clone your git repo. Please check your repo url, if it's private, "
                "please make it public or upload it in zip file."
            )
        case ErrorCodes.SpecialFoldersNotAllowed:
            print_markdown(
                "Please delete `.ebextensions` and `.platform` in your project."
            )
        case ErrorCodes.GitFolderNotAllowed:
            print_markdown("Please delete `.git` folder in your project.")
        case ErrorCodes.RequirementsTxtNotFound:
            print_markdown(
                "You need `requirements.txt` in your project, if you don't have, "
                "please create one, make sure it contains `funix`."
            )
        case ErrorCodes.NoFunixInRequirementsTxt:
            print_markdown(
                "You need `funix` in your `requirements.txt`, please add it."
            )
        case ErrorCodes.FileTooLarge:
            print_markdown(
                "File too large. Please make sure your file is less than 200MB. If you need to upload a larger file, "
                "you can use AWS or Google Cloud, or contact support@funix.io."
            )
        case ErrorCodes.FileNotFound:
            print_markdown(
                "Your python main file is not found. Please make sure your file exists and you have the correct path."
            )
        case ErrorCodes.IllegalString:
            print_markdown(
                "Your argument contains illegal characters, remove: ()[]<>:\"'/\\|?*"
            )
        case ErrorCodes.ArgumentTooLong:
            print_markdown(
                "Your argument is too long, more than 128 characters. Please shorten it."
            )
        case ErrorCodes.InstancesTooMany:
            print_markdown(
                "You already have 10 instances in your account, if you need more, please contact support@funix.io"
            )
        case ErrorCodes.DuplicationName:
            print_markdown(
                "You have already used this app name, please think more and use another one."
            )
        case ErrorCodes.InstanceNotFound:
            print_markdown("Instance not found, please check your instance id.")
        case ErrorCodes.UserHasNoInstance:
            print_markdown("You have no instance, but you can create one if you want.")
        case ErrorCodes.InstanceNotPrepared:
            print_markdown(
                "Please wait for the instance to be prepared, try again later. "
                "If your instance is still not ready after a long time, please contact support@funix.io"
            )
        case ErrorCodes.BodyNoMultiPart:
            print_markdown(
                "It seems like you didn't upload any files, please check your request."
            )
        case ErrorCodes.FileIsCleaned:
            print_markdown(
                "The file could not be found or was removed because of the 30-minute temporary file limit. "
                "Please check your fid and upload again if it was removed due to a timeout."
            )
        case ErrorCodes.InstanceNotPaused:
            print_markdown("Your instance is not paused, you cannot restore it.")
        case _:
            print_markdown(f"Unknown error code `{code}`.")
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
