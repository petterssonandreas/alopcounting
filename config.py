from os import makedirs, PathLike
from pathlib import Path

import tomlkit as toml
from git import Repo
from git.exc import InvalidGitRepositoryError

CONFIG_FILENAME = "config.toml"

DEFAULT_TOML_CONFIG: toml.TOMLDocument = toml.parse("""\
[userdata]
userdata_storage_path = "./userdata"
accounts_filename = "accounts.json"
verifications_dirname = "verifications"
""")

_toml_config = DEFAULT_TOML_CONFIG

def _is_git_repo(path: PathLike) -> bool:
    try:
        _ = Repo(path).git_dir
        return True
    except InvalidGitRepositoryError:
        return False

def config_init() -> bool:
    global _toml_config
    conf_path = Path(CONFIG_FILENAME)
    if not (conf_path.exists() and conf_path.is_file()):
        print("No config file!")
        print("Creating file with default content:")
        _toml_config = DEFAULT_TOML_CONFIG
        print(toml.dumps(_toml_config))
        with open(conf_path, "w") as conf_file:
            conf_file.write(toml.dumps(_toml_config))
        return True

    with open(conf_path, "r") as conf_file:
        print(f"Reading config from: {conf_path.absolute()}")
        _toml_config = toml.parse(conf_file.read())
        print(toml.dumps(_toml_config))

    try:
        storage_path = _toml_config["userdata"]["userdata_storage_path"]
        acc_filename = _toml_config["userdata"]["accounts_filename"]
        ver_dirname = _toml_config["userdata"]["verifications_dirname"]
    except toml.exceptions.NonExistentKey as err:
        print(f"Missing entry in config: {err}")
        return False

    if type(storage_path) is not toml.items.String:
        print(f"Incorrect type, expected string, for key: userdata/userdata_storage_path")
        return False
    if type(acc_filename) is not toml.items.String:
        print(f"Incorrect type, expected string, for key: userdata/accounts_filename")
        return False
    if type(ver_dirname) is not toml.items.String:
        print(f"Incorrect type, expected string, for key: userdata/verifications_dirname")
        return False

    dir = Path(_toml_config["userdata"]["userdata_storage_path"].value)
    if not dir.exists():
        print(f"Creating userdata dir: {dir.absolute()}")
        makedirs(dir)
    elif not dir.is_dir():
        print(f"Userdata dir is not a directory: {dir.absolute()}")
        return False

    ver_dir = config_get_verifications_storage_dir_path()
    if not ver_dir.exists():
        print(f"Creating verifications dir: {ver_dir.absolute()}")
        makedirs(ver_dir)
    elif not ver_dir.is_dir():
        print(f"Verifications dir is not a directory: {ver_dir.absolute()}")
        return False

    acc_file = config_get_accounts_storage_file_path()
    if not acc_file.exists():
        print(f"Creating accounts file: {acc_file.absolute()}")
        with open(acc_file, "w") as fp:
            fp.write("[]\n")
    elif not acc_file.is_file():
        print(f"Accounts file is not a file: {acc_file.absolute()}")
        return False

    if not _is_git_repo(dir):
        print(f"Creating git repo in userdata dir: {dir.absolute()}")
        repo = Repo.init(dir)

    return config_do_git_commit("STARTUP - Add accounts file and verifications directory")

def config_get_accounts_storage_file_path() -> Path:
    global _toml_config
    return Path(_toml_config["userdata"]["userdata_storage_path"].value) / Path(_toml_config["userdata"]["accounts_filename"].value)

def config_get_verifications_storage_dir_path() -> Path:
    global _toml_config
    return Path(_toml_config["userdata"]["userdata_storage_path"].value) / Path(_toml_config["userdata"]["verifications_dirname"].value)

def config_do_git_commit(msg: str) -> bool:
    global _toml_config
    dir = Path(_toml_config["userdata"]["userdata_storage_path"].value)
    if not _is_git_repo(dir):
        print(f"No git repository in userdata dir: {dir.absolute()}")
        return False
    else:
        repo = Repo(dir)

    if repo.is_dirty():
        repo.index.add(_toml_config["userdata"]["accounts_filename"].value)
        repo.index.add(_toml_config["userdata"]["verifications_dirname"].value)
        repo.index.commit(msg)

    return True
