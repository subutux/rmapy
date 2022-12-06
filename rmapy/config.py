from pathlib import Path
from yaml import BaseLoader
from yaml import load as yml_load
from yaml import dump as yml_dump
from typing import Dict


config_path = Path.joinpath(Path.home(), ".rmapi")
config_file_path = Path.joinpath(config_path, 'config')
config_cloudstatus_path = Path.joinpath(config_path, 'cloud')
config_meta_path = Path.joinpath(config_path, 'meta')


def load() -> dict:
    """Load the .rmapy config file"""
    config: Dict[str, str] = {}
    if Path.exists(config_file_path):
        with open(config_file_path, 'r') as config_file:
            config = dict(yml_load(config_file.read(), Loader=BaseLoader))

    return config


def dump(config: dict) -> None:
    """Dump config to the .rmapy config file

    Args:
        config: A dict containing data to dump to the .rmapi
            config file.
    """
    Path(config_path).mkdir(parents=True, exist_ok=True)
    with open(config_file_path, 'w') as config_file:
        config_file.write(yml_dump(config))


