import os
import zipfile

import requests
import rich
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from tengoku.config import read_key_from_config
from tengoku.routes import FILE_ACTIONS, INSTANCE_ACTIONS

console = Console()

STATES_MAP = {
    100: "Task Created",
    101: "Repo or File Processing",
    102: "Generating Config",
    103: "Uploading Code",
    104: "AWS EB Creating",
    200: "Success",
    400: "Failed",
}

STATUS_MAP = {
    200: "Success",
    400: "Git repo cannot clone",
    401: "Found .ebextensions folder",
    402: "Found .git folder",
    403: "Cannot found requirements.txt",
    404: "Cannot found funix",
    405: "Your code or git repo is so large, 500MB is the limit",
    406: "Cannot found entry point",
    407: "Your string has some invalid characters",
    408: "Argument is too long to handle",
    409: "Require repo link",
    410: "Require name",
    411: "Require entry point",
    412: "In close test, you only can deploy 10 instances",
    413: "Duplicate name",
    414: "Require file id",
    415: "Instance not found",
    416: "Require instance id",
    417: "Users has no instances",
    418: "No file is uploaded",
    420: "File is cleaned",
    500: "Internal Server Error",
}


def zip_folder(path: str, zip_handler: zipfile.ZipFile):
    for folder_name, subfolders, filenames in os.walk(path):
        for filename in filenames:
            if filename in ["deploy.zip", ".DS_Store", ".gitignore"]:
                continue
            if filename.endswith(".pyc"):
                continue
            if folder_name in ["__pycache__", ".git", ".ebextensions"]:
                continue
            file_path = os.path.join(folder_name, filename)
            zip_handler.write(file_path, arcname=os.path.relpath(file_path, path))


def local_deploy(
    dev_folder: str,
    name: str,
    file: str = "main.py",
    no_frontend: bool = False,
    lazy: bool = False,
    dir_mode: bool = False,
    transform: bool = False,
    app_secret: str | None = None,
):
    """
    Deploy local folder to Funix Cloud.

    Args:
        dev_folder (str): The path to the dev folder.
        name (str): The name of the instance.
        file (str, optional): The entry file to run. Defaults to "main.py".
        no_frontend (bool, optional): Whether to disable the frontend. Defaults to False.
        lazy (bool, optional): Whether to use lazy mode. Defaults to False.
        dir_mode (bool, optional): Whether to use directory mode. Defaults to False.
        transform (bool, optional): Whether to use transform mode. Defaults to False.
        app_secret (str | None, optional): The app secret. Defaults to None.
    """
    abs_path = os.path.abspath(dev_folder)
    server = read_key_from_config("server")
    token = read_key_from_config("token")
    if not token:
        print("Please login first!")
        return
    if os.path.exists("deploy.zip"):
        os.remove("deploy.zip")
    if not os.path.exists(abs_path):
        print("Dev folder not found")
        return
    with zipfile.ZipFile("deploy.zip", "w", zipfile.ZIP_DEFLATED) as zip_handler:
        zip_folder(abs_path, zip_handler)
    data = requests.post(
        server + FILE_ACTIONS["upload"],
        files={"file": ("deploy.zip", open("deploy.zip", "rb"))},
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    if "code" in data and data["code"] != 200:
        print(data["message"])
        return
    print("Successfully uploaded code!")
    file_id = data["data"]["file_id"]
    json_data = {
        "file_id": file_id,
        "name": name,
        "entry_point": file,
        "with_no_frontend": no_frontend,
        "with_lazy": lazy,
        "with_dir_mode": dir_mode,
        "with_transform": transform,
    }

    if app_secret and isinstance(app_secret, str):
        json_data["app_secret"] = app_secret

    result = requests.post(
        server + INSTANCE_ACTIONS["upload"],
        json=json_data,
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    if "code" in result and result["code"] == 200:
        print("Successfully created deployment task!")
    else:
        print("Failed to deploy!")
        rich.print(result)


def git(
    repo_link: str,
    name: str,
    file: str = "main.py",
    no_frontend: bool = False,
    lazy: bool = False,
    dir_mode: bool = False,
    transform: bool = False,
    app_secret: str | None = None,
):
    """
    Deploy git repository to Funix Cloud.

    Args:
        repo_link (str): The link to the git repository. Branches are not supported now.
        name (str): The name of the instance.
        file (str, optional): The entry file to run. Defaults to "main.py".
        no_frontend (bool, optional): Whether to disable the frontend. Defaults to False.
        lazy (bool, optional): Whether to use lazy mode. Defaults to False.
        dir_mode (bool, optional): Whether to use directory mode. Defaults to False.
        transform (bool, optional): Whether to use transform mode. Defaults to False.
        app_secret (str | None, optional): The app secret. Defaults to None.
    """
    token = read_key_from_config("token")
    if not token:
        print("Please login first!")
        return

    json_data = {
        "repo_link": repo_link,
        "name": name,
        "entry_point": file,
        "with_no_frontend": no_frontend,
        "with_lazy": lazy,
        "with_dir_mode": dir_mode,
        "with_transform": transform,
    }

    if app_secret and isinstance(app_secret, str):
        json_data["app_secret"] = app_secret

    result = requests.post(
        read_key_from_config("server") + INSTANCE_ACTIONS["git"],
        json=json_data,
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    if "code" in result and result["code"] == 200:
        print("Successfully created deployment task!")
    else:
        print("Failed to deploy!")
        rich.print(result)


def get_all_instances():
    """
    Get all instances in your account.
    """
    token = read_key_from_config("token")
    if not token:
        print("Please login first!")
        return

    result = requests.get(
        read_key_from_config("server") + INSTANCE_ACTIONS["all"],
        headers={
            "Authorization": f"Bearer {token}",
        },
    ).json()

    if "code" in result and result["code"] == 200:
        table = Table(title="Instances Dashboard")
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("Deploy Time")
        table.add_column("State")
        data = result["data"]
        for instance in data:
            table.add_row(
                str(instance["id"]),
                instance["name"],
                instance["start_time"],
                STATES_MAP[instance["state"]],
            )
        console.print(table)
    else:
        print("Failed to get all instances!")
        rich.print(result)


def query_instance(instance: int):
    """
    Query an instance in your account by id.
    """
    token = read_key_from_config("token")
    if not token:
        print("Please login first!")
        return
    result = requests.post(
        read_key_from_config("server") + INSTANCE_ACTIONS["query"],
        json={"id": instance},
        headers={
            "Authorization": f"Bearer {token}",
        },
    ).json()
    if "code" in result and result["code"] == 200:
        name = result["data"]["name"]

        start_time = result["data"]["start_time"]
        finish_time = result["data"]["done_time"]

        state = STATES_MAP[result["data"]["state"]]
        status = STATUS_MAP[result["data"]["status"]]

        url = result["data"]["entry"]

        message = result["data"]["message"]

        if not finish_time:
            finish_time = "Not finished"

        if not url:
            url = "Not finished"

        console.rule(f"Instance Info : {name} ({instance})")
        markdown = ""
        markdown += f"""- **Created Time**: {start_time}\n"""
        markdown += f"""- **Finished Time**: {finish_time}\n"""
        markdown += f"""- **State**: {state}\n"""
        markdown += f"""- **Status**: {status}\n"""
        markdown += f"""- **Deployer Message**: {message}\n"""
        markdown += f"""- **URL Point**: {url}\n"""
        markdown = Markdown(markdown)
        console.print(markdown)
    else:
        print("Failed to query instance!")
        rich.print(result)
