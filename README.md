# Funix-Cloud

Funix Cloud is a tool that helps you deploy your local or git repository to Funix Cloud.

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
pip install funix-cloud
```

## Registration

To use Funix Cloud, you will first need to register an account. This will be used to create and manage Funix Cloud instances. 
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

To log in and out, use the commands `funix-cloud login [username]` and `funix-cloud logout`.
```plaintext
> funix-cloud login myusername
Please input Password: ********
Login successful! Your token is saved.
```
## Deployment

### Single file

```bash
funix-cloud deploy main.py [Application Name, example: "my-first-app"]
```

To deploy a file, you need to provide a `requirements.txt` file to determine which dependencies to install. More details are provided below. If `requirements.txt` does not exist, you will be prompted with the option to have a `requirements.txt` with just funix created on your behalf.

### Folder

```bash
funix-cloud deploy [Local folder or git link: example: "my-project"] [Application Name, example: "my-first-app"] --file main.py
```

The `--file` option specifies the program entry file, which defaults to `main.py`. Note: To deploy a local folder, you will also need a `requirements.txt`. The file should exist in the same directory as the folder you are deploying, not inside the folder itself. 

### requirements.txt File

To deploy a file or folder, you will need a `requirements.txt` file to specify required dependencies. This file should exist in the same directory as the file or folder you are deploying. Simply add the names of any library/ packages your program uses. You can additionally specify versions of the installation. Below is an example for a project usinf dependencies funix, openai (version 1.1.1 or later), and requests.  

```plaintext
funix
openai>=1.1.1
requests
```

### Configuration File

```bash
funix-cloud run
```

Writing in a configuration file is one of the best ways to deploy a project with complex options.

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
To see a complete list of Funix Cloud commands and descriptions, run `funix-cloud` or `funix-cloud --help`. 

Common commands include `funix-cloud list` to see your current deployed instances and `funix-cloud delete [id number]` to delete an instance.

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
