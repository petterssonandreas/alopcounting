import tomlkit as toml
from pathlib import Path

CONFIG_FILENAME = "config.toml"

DEFAULT_TOML_CONFIG: toml.TOMLDocument = toml.parse("""\
[accounts]
storage_file_path = "./userdata/accounts.json"

[verifications]
storage_dir_path = "./userdata/verifications/"
""")

_toml_config = DEFAULT_TOML_CONFIG

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
        acc_conf = _toml_config["accounts"]["storage_file_path"]
        ver_conf = _toml_config["verifications"]["storage_dir_path"]
    except toml.exceptions.NonExistentKey as err:
        print(f"Missing entry in config: {err}")
        return False

    if type(acc_conf) is not toml.items.String:
        print(f"Incorrect type, expected string, for key: accounts/storage_file_path")
        return False
    if type(ver_conf) is not toml.items.String:
        print(f"Incorrect type, expected string, for key: verifications/storage_dir_path")
        return False

    return True

def config_get_accounts_storage_file_path() -> str:
    global _toml_config
    return _toml_config["accounts"]["storage_file_path"].value

def config_get_verifications_storage_dir_path() -> str:
    global _toml_config
    return _toml_config["verifications"]["storage_dir_path"].value
