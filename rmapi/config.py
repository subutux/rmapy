from pathlib import Path
from yaml import load as yml_load
from yaml import dump as yml_dump


def load() -> dict:
    """
    Load the .rmapi config file
    """

    config_file_path = Path.joinpath(Path.home(), ".rmapi")
    config = {}
    if Path.exists(config_file_path):
        with open(config_file_path, 'r') as config_file:
            config = dict(yml_load(config_file.read()))

    return config


def dump(config: dict) -> True:
    """
    Dump config to the .rmapi config file
    """

    config_file_path = Path.joinpath(Path.home(), ".rmapi")

    with open(config_file_path, 'w') as config_file:
        config_file.write(yml_dump(config))

    return True


