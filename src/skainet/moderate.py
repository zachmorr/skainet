import click
import openai

from skainet import utils
from skainet.data import CONFIG

DEFAULT_CHAT_MODEL = CONFIG["moderation"]["model"]


@click.command()
@click.argument("input", type=utils.Prompt(), default="")
@click.option(
    "-m",
    "--model",
    type=str,
    default=DEFAULT_CHAT_MODEL,
    help=f"Model selection. Default is {DEFAULT_CHAT_MODEL}.",
)
def moderate(input: str, model: str):
    """Check if text violates OpenAI's Content Policy"""
    try:
        response = openai.Moderation.create(
            input=input,
            model=model,
        )
    except openai.OpenAIError as e:
        utils.handle_error(e)
    else:
        print(response)
