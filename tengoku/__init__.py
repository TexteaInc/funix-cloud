import fire
from tengoku.user import register, login, logout
from tengoku.deploy import git, get_all_instances, query_instance


def start():
    fire.Fire({
        "user": {
            "register": register,
            "login": login,
            "logout": logout,
        },
        "instance": {
            "all": get_all_instances,
            "git": git,
            "id": query_instance
        }
    })


if __name__ == "__main__":
    start()
