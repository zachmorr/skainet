import sys
from typing import List

import click

from skainet.data import _CONFIG_FILE, CONFIG


@click.group("config", help="Skainet configuration")
def config():
    """DOCUMENTATION"""
    pass


@config.command()
def show():
    """Display contents of config file"""
    print(_CONFIG_FILE.read_text())


@config.command()
def path():
    """Show path to config file"""
    print(str(_CONFIG_FILE.absolute()))


@config.command()
@click.argument("setting", nargs=-1)
@click.argument("value", type=str)
def set(setting: List[str], value: str):
    """Set a variable in the config file"""
    config_path = setting
    try:
        dic = CONFIG
        for key in config_path[:-1]:
            dic = dic[key]
        dic[config_path[-1]] = value
    except KeyError as e:
        print(f"{' '.join(setting)} does not exist")
        sys.exit(1)

    with open(_CONFIG_FILE, "w") as configfile:
        CONFIG.write(configfile)
