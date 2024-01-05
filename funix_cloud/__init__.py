import sys
import traceback

import fire
import requests
from rich.console import Console
from rich.prompt import Confirm

from funix_deploy.cli import DeployCLI

console = Console()


def start():
    try:
        try:
            fire.Fire(DeployCLI)
        except requests.exceptions.ConnectionError as e:
            see_full = Confirm.ask("ConnectionError, maybe the server is down? Do you want to see full stacktrace?")
            if see_full:
                print()
                print(traceback.format_exc())
            sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print()
        print("Exiting..")
        sys.exit(1)


if __name__ == "__main__":
    start()
