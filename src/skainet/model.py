import sys

import click
import openai

from skainet import utils


@click.group("model", help="Get information about available models")
def model():
    """DOCUMENTATION"""
    pass


@model.command()
def list():
    """List available models"""
    try:
        model_list = openai.Model.list()["data"]
    except openai.OpenAIError as e:
        utils.handle_openai_error(e)
    else:
        click.echo("Available Models:")
        model_names = [model["id"] for model in model_list]
        for name in sorted(model_names):
            click.echo(f"{name}")


@model.command()
@click.argument("model_name", type=str)
def show(model_name: str):
    """Get information about a model"""
    try:
        model_list = openai.Model.list()["data"]
    except openai.OpenAIError as e:
        utils.handle_openai_error(e)
    else:
        model_info = {}
        for model in model_list:
            if model["id"] == model_name:
                model_info = model

        if model_info:
            click.echo(model_info)
        else:
            click.echo(f"No model with name '{model_name}' found.", err=True)
            sys.exit(1)
