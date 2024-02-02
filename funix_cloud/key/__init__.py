import os
import fire
import json
import typing
import urllib3
from urllib.parse import urlparse
import ipaddress


local_configure_file = "llamakey_local.env"
url_keys = ["OPENAI_BASE_URL", "CO_API_URL", "ANYSCALE_BASE_URL", "HF_INFERENCE_ENDPOINT", "VECTARA_BASE_URL"]

def __replace_url_with(url: str, replace_url: str) -> str:
    """
    Replace the url with the new url

    Prevent things like `0.0.0.0` or `127.0.0.1` on remote servers.

    :param url: The original url
    :param replace_url: The new url
    """
    parsed_url = urlparse(url)
    parsed_replace_url = urlparse(replace_url)

    try:
        parsed_url_ip = ipaddress.ip_address(parsed_url.hostname)
        if parsed_url_ip.is_private:
            parsed_url = parsed_url._replace(netloc=parsed_replace_url.netloc)
            if parsed_replace_url.scheme:
                parsed_url = parsed_url._replace(scheme=parsed_replace_url.scheme)
            if not parsed_url.scheme:
                parsed_url = parsed_url._replace(scheme=parsed_replace_url.scheme)
    except ValueError:
        pass

    return parsed_url.geturl()


def __replace_env(env: dict, url: str, replace_url: str) -> dict:
    """
    Ensure all urls are replaced with the new url

    :param env: The environment dictionary
    :param url: The original url
    :param replace_url: The new url
    """
    new_env = {}
    for key, value in env.items():
        if key in url_keys:
            new_env[key] = __replace_url_with(value, replace_url)
        else:
            new_env[key] = value
    return new_env


class LlaMasterKey:
    @staticmethod
    def env(url: typing.Optional[str] = os.environ.get("BASE_URL", None)):
        """
        Download environment file from server

        :param url: LlaMasterKey server url
        """
        if url:
            response = urllib3.request("GET", url.rstrip("/") + "/lmk/env?format=json")
            content = response.data.decode("utf-8")
            if response.status != 200:
                print("LlaMasterKey client encountered an error: \n\n" + content)
                return

            data = __replace_env(json.loads(content))
            env_content = ""
            for key, value in data.items():
                env_content += f"{key}=\"{value}\"\n"
            with open(".env", "w") as f:
                f.write(data)
            print(f"Environment file written to `{local_configure_file}`, now run `source {local_configure_file}`")
        else:
            print("Usage: `lmkcli env <url>` or set `BASE_URL` environment variable")

    @staticmethod
    def overwrite_env(url: str):
        """
        Overwrite environment variables with those from server (in Python runtime, not in shell)

        :param url: LlaMasterKey server url
        """
        response = urllib3.request("GET", url.rstrip("/") + "/lmk/env?format=json")
        updated_env = response.data.decode("utf-8")

        data = __replace_env(json.loads(updated_env))
        os.environ.update(data)


def __main__():
    fire.Fire(LlaMasterKey)


if __name__ == "__main__":
    __main__()
