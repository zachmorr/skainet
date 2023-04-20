import functools
import sys
from typing import Dict, List

import click
import openai

from skainet import utils
from skainet.data import CONFIG, load_chat, save_chat


def calculate_tokens(string: str) -> int:
    return len(string.split())


def calculate_context(message_list: List[Dict[str, str]]):
    return sum([calculate_tokens(msg["content"]) for msg in message_list])


def truncate_context(
    message_list: List[Dict[str, str]], context_limit: int
) -> List[Dict[str, str]]:
    context = []
    for message in reversed(message_list):
        new_tokens = calculate_tokens(message["content"])
        if calculate_context(context) + new_tokens < context_limit:
            context.insert(0, message)
        else:
            break

    return context


def text_options(model, num, temp):
    def decorator(function):
        @click.option(
            "-m",
            "--model",
            type=str,
            default=model,
            help=f"Model selection",
        )
        @click.option(
            "-n",
            "--num",
            type=click.IntRange(min=1),
            default=num,
            help=f"Number of completions to generate",
        )
        @click.option(
            "-t",
            "--temp",
            type=click.FloatRange(min=0, max=2),
            default=temp,
            help=f"Sampling temperature selection",
        )
        @functools.wraps(function)
        def wrapper_common_options(*args, **kwargs):
            return function(*args, **kwargs)

        return wrapper_common_options

    return decorator


MAXIMUM_CONTEXT = 4096
SYSTEM_MESSAGE = {
    "role": "system",
    "content": CONFIG["chat"]["seed_prompt"],
}
SYSTEM_MESSAGE_LEN = calculate_tokens(SYSTEM_MESSAGE["content"])
DEFAULT_CHAT_CONTEXT = int(CONFIG["chat"]["context"])
DEFAULT_CHAT_MODEL = CONFIG["chat"]["model"]
DEFAULT_CHAT_TEMPERATURE = int(CONFIG["chat"]["temperature"])
DEFAULT_CHAT_MAX_TOKENS = int(CONFIG["chat"]["max_tokens"])
DEFAULT_CHAT_NUM = int(CONFIG["chat"]["num"])


@click.command(context_settings={"show_default": True})
@click.argument("prompt", type=utils.Prompt(), default="")
@text_options(DEFAULT_CHAT_MODEL, DEFAULT_CHAT_NUM, DEFAULT_CHAT_TEMPERATURE)
@click.option(
    "-c",
    "--context",
    type=click.IntRange(min=1, max=MAXIMUM_CONTEXT - SYSTEM_MESSAGE_LEN),
    default=DEFAULT_CHAT_CONTEXT,
    help=f"Context length, for chat",
)
@click.option("-ch", "--clearhistory", is_flag=True, help="Clear entire chat history")
@click.option(
    "-mt",
    "--maxtokens",
    type=int,
    default=DEFAULT_CHAT_MAX_TOKENS,
    help=f"Maximum number of tokens in response, set to -1 to remove limit",
)
@click.option(
    "-s",
    "--stop",
    type=str,
    multiple=True,
    help=f"Sequences where the API will stop generating further tokens. Up to four are allowed. The returned text will not contain the stop sequence",
)
@click.option("-ns", "--no-stream", is_flag=True, help=f"Disable response streaming")
@click.option("-nu", "--no-update", is_flag=True, help=f"Do not update chat history")
def chat(
    prompt: str,
    model: str,
    num: int,
    temp: float,
    context: int,
    clearhistory: bool,
    maxtokens: int,
    stop: int,
    no_stream: bool,
    no_update: bool,
):
    """Chat with ChatGPT

    Send PROMPT to ChatGPT. PROMPT can be a string, filepath, or piped in.
    If no PROMPT is given, Skai will open $EDITOR or your configured text editor.
    """

    if clearhistory is True:
        save_chat([])

    if maxtokens < 0:
        maxtokens = None

    if not stop:
        stop = None

    # Load chat history and append new prompt
    chat_history = load_chat()
    new_prompt = {"role": "user", "content": prompt}
    chat_history.append(new_prompt)

    # Limit chat context & instert seed prompt
    available_context = context - SYSTEM_MESSAGE_LEN
    current_context = truncate_context(chat_history, available_context)
    if current_context != chat_history:
        print(
            "Warning: your chat history has been truncated to fit the context limit",
            file=sys.stderr,
        )
    current_context.insert(0, SYSTEM_MESSAGE)

    # Send request
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=current_context,
            temperature=temp,
            # top_p=args.top_p,
            n=num,
            stream=not no_stream,
            stop=stop,
            max_tokens=maxtokens,
            # presence_penalty=args.presence_penalty,
            # frequency_penalty=args.frequency_penalty,
            # user=args.user
        )
    except openai.OpenAIError as e:
        utils.handle_error(e)
    else:
        if num > 1:
            if no_stream:
                for index, choice in enumerate(response["choices"]):
                    content = choice["message"]["content"]
                    print(f"({index}) {content}")
            else:
                messages = {}
                for chunk in response:
                    for choice in chunk["choices"]:
                        index = choice["index"]
                        if index not in messages:
                            messages[index] = ""

                        delta = choice["delta"]
                        if "content" in delta:
                            content = delta["content"]
                            messages[index] += content

                for index in range(len(messages)):
                    print(f"({index}) {messages[index]}")
        else:
            if no_stream:
                new_response = response["choices"][0]["message"]
                print(new_response["content"])
            else:
                new_response = {"role": "", "content": ""}
                for chunk in response:
                    # Parse response chunk
                    choice = chunk["choices"][0]
                    delta = choice["delta"]
                    if "role" in delta:
                        new_response["role"] = delta["role"]
                        text = ""
                    elif "content" in delta:
                        new_response["content"] += delta["content"]
                        text = delta["content"]
                    elif not delta:
                        text = "\n"
                    else:
                        text = ""

                    print(text, end="")

            if not no_update:
                chat_history.append(new_response)
                chat_history = truncate_context(chat_history, MAXIMUM_CONTEXT)
                save_chat(chat_history)


DEFAULT_COMPLETE_MODEL = CONFIG["completion"]["model"]
DEFAULT_COMPLETE_SUFFIX = CONFIG["completion"]["suffix"]
DEFAULT_COMPLETE_MAX_TOKENS = int(CONFIG["completion"]["max_tokens"])
DEFAULT_COMPLETE_TEMPERATURE = int(CONFIG["completion"]["temperature"])
DEFAULT_COMPLETE_NUM = int(CONFIG["completion"]["num"])


@click.command(context_settings={"show_default": True})
@click.argument("prompt", type=utils.Prompt(), default="")
@text_options(
    DEFAULT_COMPLETE_MODEL, DEFAULT_COMPLETE_NUM, DEFAULT_COMPLETE_TEMPERATURE
)
@click.option(
    "-mt",
    "--maxtokens",
    type=int,
    default=DEFAULT_COMPLETE_MAX_TOKENS,
    help=f"Maximum number of tokens in response, set to -1 to remove limit",
)
@click.option(
    "-s",
    "--stop",
    type=str,
    multiple=True,
    help=f"Sequences where the API will stop generating further tokens. Up to four are allowed. The returned text will not contain the stop sequence.",
)
@click.option("-ns", "--no-stream", is_flag=True, help=f"Disable response streaming.")
@click.option(
    "-sf",
    "--suffix",
    type=str,
    default=DEFAULT_COMPLETE_SUFFIX,
    help=f"Suffix that comes after a completion of inserted text.",
)
@click.option(
    "--echo", is_flag=True, help=f"Echo back the prompt in addition to the completion"
)
def complete(
    prompt: str,
    model: str,
    suffix: str,
    maxtokens: int,
    temp: float,
    num: int,
    echo: bool,
    stop: List[str],
    no_stream: bool,
):
    """Text Completion

    Return a completion for a given prompt. PROMPT can be a string, filepath, or piped in.
    If no PROMPT is given, Skai will open $EDITOR or your configured text editor.
    """

    if maxtokens < 0:
        maxtokens = None

    if not suffix:
        suffix = None

    if not stop:
        stop = None

    # Send request
    try:
        response = openai.Completion.create(
            model=model,
            prompt=prompt,
            suffix=suffix,
            max_tokens=maxtokens,
            temperature=temp,
            # top_p=args.top_p,
            n=num,
            stream=not no_stream,
            # logprobs=args.logprobs,
            echo=echo,
            stop=stop,
            # presence_panalty=args.presence_penalty,
            # frequency_penalty=args.frequency_penalty,
            # best_of=args.best_of,
            # logit_bias=args.logit_bias,
        )
    except openai.OpenAIError as e:
        utils.handle_error(e)
    else:
        if num > 1:
            if no_stream:
                for index, choice in enumerate(response["choices"]):
                    text = choice["text"]
                    print(f"({index}) {text}")
            else:
                messages = {}
                for chunk in response:
                    for choice in chunk["choices"]:
                        index = choice["index"]
                        if index not in messages:
                            messages[index] = ""

                        text = choice["text"]
                        messages[index] += text

                for index, text in messages.items():
                    print(f"({index}) {text}")
        else:
            if no_stream:
                text = response["choices"][0]["text"]
                print(text, end="")
            else:
                for chunk in response:
                    text = chunk["choices"][0]["text"]
                    print(text, end="")


DEFAULT_EDIT_MODEL = CONFIG["edit"]["model"]
DEFAULT_EDIT_TEMPERATURE = int(CONFIG["edit"]["temperature"])
DEFAULT_EDIT_NUM = int(CONFIG["edit"]["num"])


@click.command(context_settings={"show_default": True})
@click.argument("instruction", type=str)
@click.argument("input", type=utils.Prompt(), default="")
@text_options(DEFAULT_EDIT_MODEL, DEFAULT_EDIT_NUM, DEFAULT_EDIT_TEMPERATURE)
def edit(instruction: str, input: str, model: str, temp: float, num: int):
    """Text editing

    Edit a given input according to the instruction. INPUT a string, filepath, or piped in.
    If no INPUT is given, Skai will open $EDITOR or your configured text editor.
    """

    # Send request
    try:
        response = openai.Edit.create(
            model=model,
            input=input,
            instruction=instruction,
            n=num,
            temperature=temp,
            # top_p=args.top_p,
        )
    except openai.OpenAIError as e:
        utils.handle_error(e)
    else:
        if num > 1:
            for choice in response["choices"]:
                print(f"({choice['index']}) {choice['text']}")
        else:
            text = response["choices"][0]["text"]
            print(text)
