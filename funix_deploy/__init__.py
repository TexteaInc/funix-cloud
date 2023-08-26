import fire

from funix_deploy.deploy import get_all_instances, git, local_deploy, query_instance
from funix_deploy.user import login, logout, register


def start():
    fire.Fire(
        {
            "user": {
                "register": register,
                "login": login,
                "logout": logout,
            },
            "instance": {
                "all": get_all_instances,
                "git": git,
                "id": query_instance,
                "local": local_deploy,
            },
        }
    )


if __name__ == "__main__":
    start()
