import requests
import rich

from tengoku.config import read_key_from_config, write_key_to_config
from tengoku.routes import USER_ACTIONS


def login(
    username: str,
    password: str,
):
    """
    Login as a user.

    Args:
        username (str): The username of the user.
        password (str): The password of the user.
    """
    result = requests.post(
        read_key_from_config("server") + USER_ACTIONS["login"],
        json={
            "username": username,
            "password": password,
        }
    ).json()

    if "code" in result and result["code"] == 200:
        token = result["data"]["token"]
        write_key_to_config("token", token)
        print("Successfully logged in! Your token is saved.")
    else:
        print("Failed to log in!")
        rich.print(result)


def register(
    username: str,
    password: str,
):
    """
    Register a new user. You will automatically be logged in after registering.

    Args:
        username (str): The username of the new user.
        password (str): The password of the new user.
    """
    result = requests.post(
        read_key_from_config("server") + USER_ACTIONS["register"],
        json={
            "username": username,
            "password": password,
        }
    ).json()
    if "code" in result and result["code"] == 200:
        print("Successfully registered!")
    else:
        print("Failed to register!")
        rich.print(result)


def logout():
    """
    Clear the token from the config file.
    """
    write_key_to_config("token", None)
    print("Successfully logged out!")
