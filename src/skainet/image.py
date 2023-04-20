import base64
import functools
import os
import platform
import sys
import tempfile
import uuid
import webbrowser
from pathlib import Path
from typing import BinaryIO

import click
import openai

from skainet import utils
from skainet.data import CONFIG

DEFAULT_NUM = int(CONFIG["image"]["num"])
DEFAULT_SIZE = CONFIG["image"]["size"]
DEFAULT_FORMAT = CONFIG["image"]["format"]

URL_CHOICES = [
    "url",
    "b64_json",
]

SIZE_CHOICES = [
    "1024x1024",
    "512x512",
    "256x256",
]


@click.group("image", help="Image generation and manipulation")
def image():
    """DOCUMENTATION"""
    pass


def image_options(function):
    @click.option(
        "-n",
        "--num",
        type=click.IntRange(min=1),
        default=DEFAULT_NUM,
        help=f"Number of images to generate. Default is {DEFAULT_NUM}",
    )
    @click.option(
        "-s",
        "--size",
        type=click.Choice(SIZE_CHOICES),
        default=DEFAULT_SIZE,
        help=f"Image size",
    )
    @click.option(
        "-fmt",
        "--format",
        type=click.Choice(URL_CHOICES),
        default=DEFAULT_FORMAT,
        help=f"Format of returned images",
    )
    @click.option(
        "-p",
        "--print",
        "print_response",
        is_flag=True,
        help="Output response to terminal instead of opening",
    )
    @functools.wraps(function)
    def wrapper_common_options(*args, **kwargs):
        return function(*args, **kwargs)

    return wrapper_common_options


@image.command(context_settings={"show_default": True})
@click.argument("prompt", type=utils.Prompt(), default="")
@image_options
def create(prompt: str, num: int, size: str, format: str, print_response: bool):
    """Image generation

    Generate an image from a PROMPT. PROMPT can be a string, filepath, or piped in.
    If no PROMPT is given, Skai will open $EDITOR or your configured text editor.
    """

    try:
        response = openai.Image.create(
            prompt=prompt,
            n=num,
            size=size,
            response_format=format,
        )
    except openai.OpenAIError as e:
        utils.handle_error(e)
    else:
        display_image_response(response, format, num, print_response)


@image.command(context_settings={"show_default": True})
@click.argument("image", type=utils.File("rb", exts=[".png"]))
@click.argument("mask", type=utils.File("rb", exts=[".png"]))
@click.argument("prompt", type=utils.Prompt(), default="")
@image_options
def edit(
    image: BinaryIO,
    mask: BinaryIO,
    prompt: str,
    num: int,
    size: str,
    format: str,
    print_response: bool,
):
    """Edit an image.

    Generate an edit from a PROMPT. PROMPT can be a string, filepath, or piped in.
    If no PROMPT is given, Skai will open $EDITOR or your configured text editor.

    IMAGE image to be editted
    MASK image with transparent areas to indicate where image should be editted
    """

    try:
        response = openai.Image.create_edit(
            image=image,
            mask=mask,
            prompt=prompt,
            n=num,
            size=size,
            response_format=format,
        )
    except openai.OpenAIError as e:
        utils.handle_error(e)
    else:
        display_image_response(response, format, num, print_response)


@image.command(
    help="Create a variation of an image", context_settings={"show_default": True}
)
@click.argument("image", type=utils.File("rb", exts=[".png"]))
@image_options
def variation(
    image: BinaryIO,
    num: int,
    size: str,
    format: str,
    print_response: bool,
):
    """DOCUMENTATION"""
    input_image = image.read()

    try:
        response = openai.Image.create_variation(
            image=input_image,
            n=num,
            size=size,
            response_format=format,
        )
    except openai.OpenAIError as e:
        utils.handle_error(e)
    else:
        display_image_response(response, format, num, print_response)


def display_image_response(response, format, num, print_response):
    for index, generation in enumerate(response["data"]):
        if format == "url":
            image = generation[format]
        elif format == "b64_json":
            b64_encoded_data = generation[format]
            decoded_image = base64.b64decode(b64_encoded_data)
            temp_file = Path(tempfile.gettempdir()) / str(uuid.uuid4())
            temp_file = temp_file.with_suffix(".png")
            temp_file.write_bytes(decoded_image)
            image = temp_file

        if print_response is True:
            if num > 1:
                print(f"({index}): {image}")
            else:
                print(f"{image}")
        else:
            try:
                if format == "b64_json":
                    image = image.as_uri()

                webbrowser.open(image)
            except Exception as e:
                print(f"Error opening image: {e}")
                sys.exit(1)
