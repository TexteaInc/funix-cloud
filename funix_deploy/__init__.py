import sys
import traceback

import fire
import requests
from rich.console import Console

from funix_deploy.cli import DeployCLI

console = Console()


def start():
    try:
        fire.Fire(DeployCLI)
    except (EOFError, KeyboardInterrupt):
        print()
        print("Exiting..")
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        i = input("ConnectionError, maybe the server is down? Did you want to see full stacktrace? [y/N]")
        if i.lower() == "y":
            print()
            print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    # console.print(
    #     Markdown(
    #         "Cannot run this file directly. Please use the command `funix-deploy` instead."
    #     )
    # )
    # sys.exit(1)
    start()
