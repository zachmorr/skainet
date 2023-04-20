import functools
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Callable, List, Optional

import click
import openai

from skainet.data import CONFIG


def create_tempfile(ext: str) -> Path:
    temp_file = Path(tempfile.gettempdir()) / str(uuid.uuid4())
    temp_file = temp_file.with_suffix(ext)
    temp_file.touch()
    return temp_file


def open_editor():
    temp_file = create_tempfile(".txt")

    if "EDITOR" in os.environ:
        editor = os.environ["EDITOR"]
    else:
        editor = CONFIG["general"]["editor"]

    subprocess.run([editor, str(temp_file)], check=True)

    return temp_file.read_text()


def handle_error(error: openai.OpenAIError):
    print(f"{error.__class__.__name__}: {error}")
    sys.exit(1)


class File(click.File):
    """
    Adding extra arguments to the click.File type to support file extension validation
    """

    def __init__(self, *args, exts: List[str], **kwargs):
        self.valid_ext = exts
        super().__init__(*args, **kwargs)

    def convert(self, value, param, ctx):
        file = super().convert(value, param, ctx)
        if self.valid_ext:
            extention = Path(file.name).suffix
            if extention not in self.valid_ext:
                self.fail(
                    f"{extention} is not a supported file type for this command",
                    param,
                    ctx,
                )
        return file


class Prompt(click.ParamType):
    name = "prompt"

    def convert(self, value: str, param, ctx):
        if not sys.stdin.isatty():
            if value:
                value = value + "\n"
            value += sys.stdin.read()

        if not value:
            value = open_editor()

        return value
