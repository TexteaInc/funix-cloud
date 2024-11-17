import os
import json

from funix_cloud.api import API
from funix_cloud.config import ConfigDict
from funix import funix_method
from funix.session import set_global_variable
from funix.hint import Markdown
from funix.util.text import un_indent

from ipywidgets import Password

from funix_cloud.util import check_username, check_email, check_password, check_password_web


config = ConfigDict(os.path.expanduser("~/.config/funix-cloud/config.json"))
api = API(config.get("api_server", "https://cloud-dev.funix.io"))
token = config.get("token", None)

class FunixCloud:
    @staticmethod
    @funix_method(default=True, title="Welcome to Funix Cloud", just_run=True)
    def welcome() -> Markdown:
        return un_indent(
            """
            # Funix Cloud Local Web Tool
            
            Welcome to Funix Cloud! This is a web tool made with Funix to manage your Funix Cloud account.
            
            You can use this tool to manage your Funix Cloud account, deploy your projects, and more.
            
            ## Getting Started
            
            You can use the following commands to get started:
            
            - [Login to Funix Cloud](/FunixCloud/login)
            - [Deploy a funix project](/FunixCloud/deploy)
            - [List all deployments](/FunixCloud/list)
            
            ## Note
            
            This tool is still in development. If you encounter any issues, please report them to the issue tracker on the [GitHub repository](https://github.com/TexteaInc/funix-cloud).
            """
        )
    
    @funix_method(disable=True)
    def __init__(self) -> None:
        pass
    
    @staticmethod
    @funix_method(title="Register to Funix Cloud")
    def register(username: str, email: str, password: Password) -> Markdown:
        if not check_username(username):
            return "Invalid username. Username must be between 5 and 50 characters and can only contain numbers, letters, underscores, and hyphens."
        if not check_email(email):
            return "Invalid email, please enter a valid email address."
        
        if not check_password(password.value):
            result = check_password_web(password.value)
            def get_mark_list(result: bool):
                return "[x]" if result else "[]"
            return un_indent(
                f"""
                Invalid password, your code must meet two of the following conditions:
                
                ---
                
                - {get_mark_list(result[0])} At least 8 characters, and at most 64 characters. This is a mandatory requirement.
                - {get_mark_list(result[1])} Contains at least one uppercase letter.
                - {get_mark_list(result[2])} Contains at least one lowercase letter.
                - {get_mark_list(result[3])} Contains at least one number.
                - {get_mark_list(result[4])} Contains at least one special character.
                """
            )
        
        register_result = api.register(username, password)
        if register_result["code"] != 0:
            return F"""We encountered an error while registering your account. Here is the error message:\n\n```json\n{json.dumps(register_result)}\n```"""
        
        login_result = api.login(username, password)
        if login_result["code"] != 0:
            return F"""We encountered an error while logging in. Here is the error message:\n\n```json\n{json.dumps(login_result)}\n```"""
        
        token = login_result["data"]["token"]
        config.set("token", token)
        
        email_result = api.bind_email(email)
        if email_result["code"] != 0:
            return F"""We encountered an error while sending verification to your email. Here is the error message:\n\n```json\n{json.dumps(email_result)}\n```"""
        else:
            return "Successfully registered and logged in. Please check your email for verification."
    
    @staticmethod
    @funix_method(title="Login to Funix Cloud")
    def login(username: str, password: Password) -> Markdown:
        login_result = api.login(username, password.value)
        if login_result["code"] != 0:
            return F"""We encountered an error while logging in. Here is the error message:\n\n```json\n{json.dumps(login_result)}\n```"""
        
        token = login_result["data"]["token"]
        config.set("token", token)
        return "Successfully logged in."
