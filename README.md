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
funix-cloud deploy main.py my-first-app
```

We need you to provide a `requirement.txt` file to determine which dependencies to install. If `requirement.txt` does not exist, we will prompt you whether to create a `requirement.txt` with just funix.

### Folder

```bash
funix-cloud deploy my-project my-first-app --file main.py
```

For local folder, we also need a `requirement.txt`. And the `--file` option specifies the program entry file, which defaults to `main.py`.

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
