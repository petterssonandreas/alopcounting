from os import makedirs, PathLike
from pathlib import Path
from glob import iglob
from typing import Iterator

import tomlkit as toml
from git import Repo
from git.exc import InvalidGitRepositoryError

CONFIG_FILENAME = "config.toml"

DEFAULT_TOML_CONFIG: toml.TOMLDocument = toml.parse("""\
[userdata]
userdata_storage_path = "./userdata"
accounts_filename = "accounts.json"
base_accounts_filename = "base_accounts.json"

[info]
company_name = "CompAny Inc"
company_number = "800000-0000"
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
        base_acc_filename = _toml_config["userdata"]["base_accounts_filename"]
        company_name = _toml_config["info"]["company_name"]
        company_number = _toml_config["info"]["company_number"]
    except toml.exceptions.NonExistentKey as err:
        print(f"Missing entry in config: {err}")
        return False

    if type(storage_path) is not toml.items.String:
        print(f"Incorrect type, expected string, for key: userdata/userdata_storage_path")
        return False
    if type(acc_filename) is not toml.items.String:
        print(f"Incorrect type, expected string, for key: userdata/accounts_filename")
        return False
    if type(base_acc_filename) is not toml.items.String:
        print(f"Incorrect type, expected string, for key: userdata/base_accounts_filename")
        return False
    if type(company_name) is not toml.items.String:
        print(f"Incorrect type, expected string, for key: info/company_name")
        return False
    if type(company_number) is not toml.items.String:
        print(f"Incorrect type, expected string, for key: info/company_number")
        return False

    dir = Path(_toml_config["userdata"]["userdata_storage_path"].value)
    if not dir.exists():
        print(f"Creating userdata dir: {dir.absolute()}")
        makedirs(dir)
    elif not dir.is_dir():
        print(f"Userdata dir is not a directory: {dir.absolute()}")
        return False

    if not _is_git_repo(dir):
        print(f"Creating git repo in userdata dir: {dir.absolute()}")
        repo = Repo.init(dir)

    return config_do_git_commit("STARTUP - Add accounts and verifications")

def config_get_accounts_iterator() -> Iterator[str]:
    global _toml_config
    return iglob(_toml_config["userdata"]["userdata_storage_path"].value + "/**/" + _toml_config["userdata"]["accounts_filename"].value)

def config_get_verifications_dir_iterator() -> Iterator[str]:
    global _toml_config
    return iglob(_toml_config["userdata"]["userdata_storage_path"].value + "/**")

def config_get_accounts_path(year: int) -> Path:
    global _toml_config
    return Path(_toml_config["userdata"]["userdata_storage_path"].value) / Path(str(year)) / Path(_toml_config["userdata"]["accounts_filename"].value)

def config_get_base_accounts_path() -> Path:
    global _toml_config
    return Path(_toml_config["userdata"]["userdata_storage_path"].value) / Path(_toml_config["userdata"]["base_accounts_filename"].value)

def config_get_verifications_dir_path(year: int) -> Path:
    global _toml_config
    return Path(_toml_config["userdata"]["userdata_storage_path"].value) / Path(str(year))

def config_get_company_name() -> str:
    global _toml_config
    return _toml_config["info"]["company_name"].value

def config_get_company_number() -> str:
    global _toml_config
    return _toml_config["info"]["company_number"].value

def config_do_git_commit(msg: str) -> bool:
    global _toml_config
    dir = Path(_toml_config["userdata"]["userdata_storage_path"].value)
    if not _is_git_repo(dir):
        print(f"No git repository in userdata dir: {dir.absolute()}")
        return False
    else:
        repo = Repo(dir)

    if repo.is_dirty() or repo.untracked_files:
        repo.git.add(all=True)
        repo.index.commit(msg)

    return True
