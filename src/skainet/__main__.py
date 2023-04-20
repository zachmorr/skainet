import os

import click
import openai
from importlib_metadata import version

from skainet.audio import audio
from skainet.config import config
from skainet.data import load_key, save_key
from skainet.file import file
from skainet.image import image
from skainet.model import model
from skainet.moderate import moderate
from skainet.text import chat, complete, edit


@click.group(invoke_without_command=True)
@click.version_option(version("skainet"))
@click.option("--key", "new_key", is_flag=True, help="Show prompt to save an API key")
def main(new_key: bool):
    """Skainet - Shell tool for interacting with the OpenAI API"""

    if "OPENAI_API_KEY" in os.environ:
        key = os.environ["OPENAI_API_KEY"]
    else:
        key = load_key()

    if new_key or not key:
        key = input(
            "Please enter your API key\nTo generate an API key, see:\nhttps://platform.openai.com/account/api-keys\n:"
        )
        save_key(key)

    openai.api_key = key


main.add_command(chat)
main.add_command(edit)
main.add_command(complete)
main.add_command(config)
main.add_command(image)
main.add_command(model)
main.add_command(moderate)
main.add_command(file)
main.add_command(audio)


if __name__ == "__main__":
    main()
