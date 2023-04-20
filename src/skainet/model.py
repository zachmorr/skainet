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
        utils.handle_error(e)
    else:
        print("Available Models:")
        model_names = [model["id"] for model in model_list]
        for name in sorted(model_names):
            print(f"{name}")


@model.command()
@click.argument("model_name", type=str)
def show(model_name: str):
    """Get information about a model"""
    try:
        model_list = openai.Model.list()["data"]
    except openai.OpenAIError as e:
        utils.handle_error(e)
    else:
        model_info = {}
        for model in model_list:
            if model["id"] == model_name:
                model_info = model

        if model_info:
            print(model_info)
        else:
            print(f"No model with name '{model_name}' found.")
            sys.exit(1)
