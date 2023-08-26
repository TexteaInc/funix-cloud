import getpass

import requests
import rich

from funix_deploy.config import read_key_from_config, write_key_to_config
from funix_deploy.routes import USER_ACTIONS


def __login(username: str, password: str):
    result = requests.post(
        read_key_from_config("server") + USER_ACTIONS["login"],
        json={
            "username": username,
            "password": password,
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

    if "code" in result and result["code"] == 200:
        token = result["data"]["token"]
        write_key_to_config("token", token)
        print("Successfully logged in! Your token is saved.")
    else:
        print("Failed to log in!")
        rich.print(result)


def register(
    username: str,
):
    """
    Register a new user. You will automatically be logged in after registering.

    Args:
        username (str): The username of the new user.
    """
    password = getpass.getpass("Password: ")
    result = requests.post(
        read_key_from_config("server") + USER_ACTIONS["register"],
        json={
            "username": username,
            "password": password,
        },
    ).json()
    if "code" in result and result["code"] == 200:
        print("Successfully registered!")
        login_result = __login(username, password)
        write_key_to_config("token", login_result["data"]["token"])
    else:
        print("Failed to register!")
        rich.print(result)


def logout():
    """
    Clear the token from the config file.
    """
    write_key_to_config("token", None)
    print("Successfully logged out!")
