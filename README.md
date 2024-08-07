# Funix-Cloud

> It's only in the development stage right now, and development may be behind Kumo (Funix-Cloud).

Funix Cloud Tool, help you deploy your local or git repository to Funix Cloud.

## Requirements

- Python 3.10+
- Internet Connection

## Installation

Currently, we only provide Git installation:

```bash
git clone https://github.com/TexteaInc/funix-cloud
cd funix-cloud
pip install -e .
```

In the future, we will support Pip installation:

```bash
pip install
```

## Registration

```plaintext
> funix-cloud register
What is a user name you preferred: myusername
What is your email: myemail@gmail.com
Password: ********
Confirm Password: ********
Login successful! Your token is saved.
Sending verification email...
Your email myemail@gmail.com will receive a verification link, please check your inbox.
```

Funix will then email you a link to click to complete your registration.

## Deployment

### Single file

```bash
funix-cloud deploy main.py [Application Name, example: "my-first-app"]
```

We need you to provide a `requirement.txt` file to determine which dependencies to install. If `requirement.txt` does not exist, we will prompt you whether to create a `requirement.txt` with just funix.

### Folder

```bash
funix-cloud deploy [Local folder or git link: example: "my-project"] [Application Name, example: "my-first-app"] --file main.py
```

For local folder, we also need a `requirement.txt`. And the `--file` option specifies the program entry file, which defaults to `main.py`.

### Configuration File

```bash
funix-cloud run
```

Writing complex options in a configuration file is one of the best ways to deploy a project.

Create a new file `kumo.toml` with these content:

```toml
[main]
name = "hello-funix"    # Application Name
entry = "main.py"       # Entry file
```

And run `funix-cloud run` in your console, all is well! For more information read [config.md](config.md).

### Git

```bash
funix-cloud deploy https://github.com/myusername/myrepo.git my-git-app --file main.py
```

Deploying a git project is similar to deploying a local folder, just from a different source.

## Other operations

```bash
# list deployed instances
funix-cloud list
# delete an instance, the 1 is instance id,
# you can query it through the list command above.
funix-cloud delete 1
```

## For LMK

If you need use remote LlaMasterKey server (like in your company network or in the future on kumo), you need `funix-cloud` to help you getting the env file.

After installing the `funix-cloud`, `lmkc` command should be available:

```bash
# For example
lmkc env https://remote.lmk.sh/
# It will get env file from https://remote.lmk.sh/, and save it in your current folder with name `llamakey_local.env`.
# If you don't want to fill the url argument, you can fill a system env called `BASE_URL` with remote lmk server.
```

Now you use it before call your python script with these:

```bash
source llamakey_local.env
python3 your_code.py
```

If you don't like doing this in command line, you can use module:

```python
from funix_cloud.key import LlaMasterKey

LlaMasterKey.overwrite_env("https://remote.lmk.sh/")  # Your remote lmk server


# Here is your code, this is an example
from huggingface_hub import InferenceClient

client = InferenceClient()
print(client.translation("My name is Sarah and I live in London", model="t5-small"))
```
