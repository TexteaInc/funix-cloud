import sys

import fire
from rich.console import Console
from rich.markdown import Markdown

from funix_deploy.cli import DeployCLI

console = Console()


def start():
    try:
        fire.Fire(DeployCLI)
    except KeyboardInterrupt:
        print()
        print("^C")
        sys.exit(1)
    except EOFError:
        print()
        print("^D")
        sys.exit(1)


if __name__ == "__main__":
    # console.print(
    #     Markdown(
    #         "Cannot run this file directly. Please use the command `funix-deploy` instead."
    #     )
    # )
    # sys.exit(1)
    start()
