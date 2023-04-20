import json
import os
import platform
import sys
from configparser import ConfigParser
from pathlib import Path
from typing import Dict, List

## Data Directory
if platform.system() == "Windows":
    appdata = os.getenv("LOCALAPPDATA")
    DATA_DIR = Path(appdata) / __package__
else:
    DATA_DIR = Path.home() / ".local" / "share" / __package__

try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except OSError as e:
    print(f"Error while attempting to create data directory: {e}")
    sys.exit(1)


## Key File
_KEY_FILE = DATA_DIR / "api_key"
if not _KEY_FILE.exists():
    _KEY_FILE.touch()


def load_key() -> str:
    return _KEY_FILE.read_text()


def save_key(key: str):
    _KEY_FILE.write_text(key)


## Chat History
_CHAT_FILE = DATA_DIR / "chat_history.json"
if not _CHAT_FILE.exists():
    _CHAT_FILE.write_text("[]")


def load_chat() -> List[Dict[str, str]]:
    with open(_CHAT_FILE) as file:
        chat = json.load(file)
    return chat


def save_chat(chat: List[Dict[str, str]]):
    with open(_CHAT_FILE, "w") as file:
        json.dump(chat, file, indent=2)


# Configuration
default_config_path = Path(__file__).parent / "config.ini"
if not default_config_path.exists():
    print(f"Default config ({default_config_path}) does not exist!")
    sys.exit(1)

DEFAULT_CONFIG = ConfigParser()
DEFAULT_CONFIG.read(default_config_path)


# Create config file, copying default config if it doesn't exist
_CONFIG_FILE = DATA_DIR / "config.ini"
if not _CONFIG_FILE.exists():
    if platform.system() == "Darwin":
        DEFAULT_CONFIG["general"]["editor"] = "open"
    elif platform.system() == "Windows":
        DEFAULT_CONFIG["general"]["editor"] = "notepad"
        editor = "notepad.exe"
    else:
        DEFAULT_CONFIG["general"]["editor"] = "nano"

    with open(_CONFIG_FILE, "w") as configfile:
        DEFAULT_CONFIG.write(configfile)

CONFIG = ConfigParser()
CONFIG.read(_CONFIG_FILE)


# Add any settings in default_config that don't exist in config file
for section in DEFAULT_CONFIG.sections():
    if section not in CONFIG:
        CONFIG.add_section(section)

    for key, value in DEFAULT_CONFIG.items(section):
        if key not in CONFIG[section]:
            CONFIG[section][key] = value

with open(_CONFIG_FILE, "w") as configfile:
    CONFIG.write(configfile)
