import getpass

import requests
import rich

from rich.markdown import Markdown

from funix_deploy.config import read_key_from_config, write_key_to_config
from funix_deploy.routes import USER_ACTIONS


console = rich.console.Console()


def __login(username: str, password: str):
    result = requests.post(
        read_key_from_config("server") + USER_ACTIONS["login"],
        json={
            "username": username,
            "password": password,
        },
    ).json()
    return result


def __bind(email: str, token: str):
    result = requests.post(
        read_key_from_config("server") + USER_ACTIONS["email_bind"],
        json={
            "email": email,
        },
        headers={
            "Authorization": f"Bearer {token}",
        }
    ).json()
    return result


def req_me(token: str):
    result = requests.post(
        read_key_from_config("server") + USER_ACTIONS["me"],
        headers={
            "Authorization": f"Bearer {token}",
        }
    ).json()
    return result


def __change_password(old_password: str, new_password: str, token: str):
    result = requests.post(
        read_key_from_config("server") + USER_ACTIONS["password_change"],
        json={
            "old_password": old_password,
            "new_password": new_password,
        },
        headers={
            "Authorization": f"Bearer {token}",
        }
    ).json()
    return result


def __forget_password(username: str, email: str):
    result = requests.post(
        read_key_from_config("server") + USER_ACTIONS["password_forget"],
        json={
            "username": username,
            "email": email,
        },
    ).json()
    return result


def __ticket(ticket: str, code: int, new_password: str):
    result = requests.post(
        read_key_from_config("server") + USER_ACTIONS["ticket"],
        json={
            "ticket": ticket,
            "code": code,
            "password": new_password,
        },
    ).json()
    return result


def login(username: str):
    """
    Login as a user.

    Args:
        username (str): The username of the user.
    """
    password = getpass.getpass("Password: ")
    result = __login(username, password)

    if "code" in result and result["code"] == 0:
        token = result["data"]["token"]
        write_key_to_config("token", token)
        print("Successfully logged in! Your token is saved.")
    else:
        print("Failed to log in!")
        rich.print(result)


def change_password():
    """
    Change your password.
    """
    token = read_key_from_config("token")
    if not token:
        print("Please login first!")
        return

    old_password = getpass.getpass("Old password: ")
    new_password = getpass.getpass("New password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    if not old_password or not new_password:
        print("Password cannot be empty!")
        return

    if new_password != confirm_password:
        print("Passwords do not match!")
        return

    if old_password == new_password:
        print("New password cannot be the same as the old one!")
        return

    result = __change_password(old_password, new_password, token)
    if "code" in result and result["code"] == 0:
        print("Successfully changed your password!")
    else:
        print("Failed to change your password!")
        rich.print(result)


def forget_password(username: str, email: str):
    """
    Forget your password. You will receive a verification code in your email.

    Args:
        username (str): The username of the user.
        email (str): The email of the user.
    """
    result = __forget_password(username, email)
    if "code" in result and result["code"] == 0:
        print(f"Successfully sent the verification code! Here is your ticket: {result['data']['ticket']}")
        print(f"Use `funix-deploy user ticket f{result['data']['ticket']} [code]` to reset your password.")
    else:
        print("Failed to send the verification code!")
        rich.print(result)


def ticket(ticket: str, code: int):
    """
    Use your ticket and verification code to reset your password.

    Args:
        ticket (str): The ticket you received.
        code (int): The verification code you received.
    """
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    if not password:
        print("Password cannot be empty!")
        return

    if password != confirm_password:
        print("Passwords do not match!")
        return

    result = __ticket(ticket, code, password)

    if "code" in result and result["code"] == 0:
        print("Successfully reset your password!")
    else:
        print("Failed to reset your password!")
        rich.print(result)


def register(
    username: str,
    email: str,
):
    """
    Register a new user. You will automatically be logged in after registering.

    Args:
        username (str): The username of the new user.
        email (str): The email of the new user.
    """
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    if not password:
        print("Password cannot be empty!")
        return

    if password != confirm_password:
        print("Passwords do not match!")
        return

    result = requests.post(
        read_key_from_config("server") + USER_ACTIONS["register"],
        json={
            "username": username,
            "password": password,
        },
    ).json()
    if "code" in result and result["code"] == 0:
        print("Successfully registered!")
        login_result = __login(username, password)
        write_key_to_config("token", login_result["data"]["token"])
        print("Try to bind your email to your account.")
        bind_result = __bind(email, login_result["data"]["token"])
        if bind_result["code"] == 0:
            print("Please check your email, you will receive a verification link.")
        else:
            print("Failed to bind your email. Try to use `funix-deploy user bind [email]` manually.")
            rich.print(bind_result)
    else:
        print("Failed to register!")
        rich.print(result)


def bind(email: str):
    """
    Bind your email to your account. You can use this command to re-send the verification link, or change email of your account.

    Args:
        email (str): The email of the user.
    """
    token = read_key_from_config("token")
    if not token:
        print("Please login first!")
        return
    result = __bind(email, token)
    if result["code"] == 0:
        print("Please check your email, you will receive a verification link.")
    else:
        print("Failed to bind your email!")
        rich.print(result)


def me():
    """
    Get your user info.
    """
    token = read_key_from_config("token")
    if not token:
        print("Please login first!")
        return
    result = req_me(token)
    if result["code"] == 0:
        markdown = ""
        markdown += f"""- **ID**: {result['data']['id']}\n"""
        markdown += f"""- **Username**: {result['data']['username']}\n"""
        if result['data']['email']:
            markdown += f"""- **Email**: {result['data']['email']}\n"""
        else:
            markdown += f"""- **Email**: Not binded yet\n"""
        console.print(Markdown(markdown))
    else:
        print("Failed to get your info!")
        rich.print(result)


def logout():
    """
    Clear the token from the config file.
    """
    write_key_to_config("token", None)
    print("Successfully logged out!")
