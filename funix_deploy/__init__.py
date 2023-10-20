import fire

from funix_deploy.deploy import get_all_instances, git, local_deploy, query_instance
from funix_deploy.user import login, logout, register, bind, me, change_password, forget_password, ticket


def start():
    fire.Fire(
        {
            "user": {
                "register": register,
                "login": login,
                "logout": logout,
                "bind": bind,
                "me": me,
                "change-password": change_password,
                "forget-password": forget_password,
                "ticket": ticket,
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
