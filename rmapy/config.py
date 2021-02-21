from pathlib import Path
from yaml import BaseLoader
from yaml import load as yml_load
from yaml import dump as yml_dump
from typing import Dict


def load() -> dict:
  """Load the .rmapy config file"""
  config_file_path = Path.joinpath(Path.home(), ".rmapi")
  config: Dict[str, str] = {}
  if Path.exists(config_file_path):
    with open(config_file_path, 'r') as config_file:
      config = dict(yml_load(config_file.read(), Loader=BaseLoader))
  return config


def dump(config: dict) -> None:
  """Dump config to the .rmapy config file

  Args:
    config: A dict containing data to dump to the .rmapy
      config file.
  """
  config_file_path = Path.joinpath(Path.home(), ".rmapi")
  with open(config_file_path, 'w') as config_file:
    config_file.write(yml_dump(config))


