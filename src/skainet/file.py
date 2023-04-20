import itertools
from pathlib import Path

import click
import openai

from skainet import utils

FILE_PURPOSES = [
    "fine-tune",
]


@click.group(help="File management")
def file():
    pass


@file.command()
def list():
    """List files"""
    try:
        response = openai.File.list()
    except openai.OpenAIError as e:
        utils.handle_error(e)
    else:
        if response["data"]:
            print("Files:")
            for file in response["data"]:
                print(file)
        else:
            print("No files")


@file.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-p",
    "--purpose",
    type=click.Choice(FILE_PURPOSES),
    default="fine-tune",
    help="Purpose of file",
)
def upload(
    file: Path,
    purpose: str,
):
    """Upload file"""
    try:
        response = openai.File.create(
            file=file.read_text(), purpose=purpose, user_provided_filename=file.name
        )
    except openai.OpenAIError as e:
        utils.handle_error(e)
    else:
        print(response)


@file.command()
@click.argument("file_id", metavar="ID", type=str)
def delete(
    file_id: str,
):
    """Delete file"""
    try:
        openai.File.delete(
            sid=file_id,
        )
    except openai.OpenAIError as e:
        utils.handle_error(e)
    else:
        pass


@file.command()
@click.argument("file_id", metavar="ID", type=str)
@click.option(
    "-o",
    "--output",
    type=click.Path(writable=True, path_type=Path),
    help="Override output file destination",
)
def download(file_id: str, output: Path):
    """Download file"""
    try:
        response_bytes = openai.File.download(
            id=file_id,
        )

        if not output or output.is_dir():
            file_list = openai.File.list()
            for file_info in file_list["data"]:
                if file_info["id"] == file_id:
                    file_name = file_info["filename"]

            if not output:
                output = Path.cwd() / file_name
            else:
                output = output / file_name
    except openai.OpenAIError as e:
        utils.handle_error(e)
    else:
        if output.exists():
            for num in itertools.count(start=1):
                test_file = output.parent / (output.stem + f"{num}" + output.suffix)
                if not test_file.exists():
                    output = test_file
                    break

        output.write_bytes(response_bytes)


@file.command()
@click.argument("name", type=str)
@click.argument("size", type=int)
@click.argument("purpose", type=click.Choice(FILE_PURPOSES), default="fine-tune")
def find(
    name: str,
    size: int,
    purpose: str,
):
    """File information"""
    try:
        response = openai.File.find_matching_files(
            name=name,
            bytes=size,
            purpose=purpose,
        )
    except openai.OpenAIError as e:
        utils.handle_error(e)
    else:
        for file in response:
            print(file)
