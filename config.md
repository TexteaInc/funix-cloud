# Kumo config file

```toml
[main]
name = "hello-funix"
entry = "main.py"
```

This is a minimized version of `kumo.toml` for most situations.

The `main` section must be exist. `name` filed is mandatory, you need to fill in the project name.

`entry` is optional, if it does not exist then `main.py` is automatically used as the entry file.

## Config

You can add advanced settings via `config` section. Here is an example:

```toml
[main]
name = "hello-funix"
entry = "main.py"

[config]
no_frontend = false
transform = false
secret = "secret"
env = ".env"
```

Each of these fields is optional.

- `no_frontend`: Boolean type, whether or not to turn off the frontend, which can be turned on if you want to deploy a Funix application with no interface and only using WebAPI. Default is `false`.
- `transform`: Boolean type, whether to enable the transformation of global variables to session variables, may fail, recommended to use `funix_class` to manage sessions. Default is `false`.
- `secret`: String type, the secret key, which is required to call the functions. Default is `null`.
- `env`: String type, the `.env` file, `funix-cloud` can access this file to read the environment information. Default is `null`. However, `funix-cloud` automatically tries to read `.env` in the current directory, and you can set `false` to disable this default action.
