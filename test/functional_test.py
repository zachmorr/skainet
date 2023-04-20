import pytest
import os
import subprocess
from pathlib import Path
import platform
import shutil
import requests
from configparser import ConfigParser
import importlib_metadata
import click
from click.testing import CliRunner
from skainet.__main__ import main
from skainet import utils
from skainet.audio import RESPONSE_FORMAT_CHOICES
from skainet.image import SIZE_CHOICES, URL_CHOICES
from skainet.data import load_key, save_key, load_chat, CONFIG, _CONFIG_FILE


# Verify that executable has already been built
repo = Path(__file__).parent.parent
if platform.system() == "Windows":
    EXE = repo / "dist" / "skainet" / f"skai.exe"
else:
    EXE = repo / "dist" / "skainet" / f"skai"

if not EXE.exists():
    pytest.fail("Executable not built")
else:
    EXE = str(EXE)


# Verify that api_key exists
if "OPENAI_API_KEY" in os.environ:
    API_KEY = os.environ["OPENAI_API_KEY"]
else:
    API_KEY = load_key()

if not API_KEY:
    pytest.fail("No API key saved")


# Verify required applications are installed and available
if not shutil.which("ffmpeg"):
    raise pytest.fail("ffmpeg isn't installed")


# Simple test to verify that built executable can run & is the correct version
def test_exe_help():
    subprocess.run([EXE, "--help"], capture_output=True, check=True)

def test_exe_version():
    ps = subprocess.run([EXE, "--version"], capture_output=True, check=True)
    exe_version = ps.stdout.split()[2].decode()
    pkg_vesion = importlib_metadata.version("skainet")
    assert exe_version == pkg_vesion, "Exe version mismatch"


@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def audio_file():
    audio_file = Path(__file__).parent / "files" / "bruh.mp3"
    if not audio_file.exists():
        raise FileNotFoundError("unable to find bruh.mp3")

    return str(audio_file)

@pytest.fixture
def image_file():
    image_file = Path(__file__).parent / "files" / "img.png"
    if not image_file.exists():
        raise FileNotFoundError("unable to find img.png")

    return str(image_file)

@pytest.fixture
def mask_file():
    mask_file = Path(__file__).parent / "files" / "mask.png"
    if not mask_file.exists():
        raise FileNotFoundError("unable to find mask.png")

    return str(mask_file)

@pytest.fixture
def jsonl_file():
    jsonl_file = Path(__file__).parent / "files" / "chat.jsonl"

    if not jsonl_file.exists():
        jsonl = """{ "prompt": "aa", "completion": "bb" }\n{ "prompt": "cc", "completion": "dd" }"""
        jsonl_file.write_text(jsonl)

    return str(jsonl_file)

class Test_Main:
    def test_help(self, runner: CliRunner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0, result.stderr

    def test_version(self, runner: CliRunner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0, result.stderr

        version = result.stdout.split()[2]
        assert version == importlib_metadata.version("skainet")

    def test_key(self, runner: CliRunner):
        save_key("")
        result = runner.invoke(main, ["--key"], input=f"{API_KEY}\n")
        assert result.exit_code == 0, result.stderr
        assert load_key() == API_KEY

    class Test_Audio:
        def test_help(self, runner: CliRunner):
            result = runner.invoke(main, ["audio", "--help"])
            print(result.output)
            assert result.exit_code == 0, result.stderr

        class Test_Transcribe:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["audio", "transcribe", "--help"])
                assert result.exit_code == 0, result.stderr

            def test_transcribe(self, runner: CliRunner, audio_file: str):
                result = runner.invoke(main, ["audio", "transcribe", audio_file])
                assert result.exit_code == 0, result.stderr
                assert result.stdout.lower() == "bruh\n"

            def test_transcribe_prompt(self, runner: CliRunner, audio_file: str):
                result = runner.invoke(main, ["audio", "transcribe", audio_file, "--prompt", "test"])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

            def test_transcribe_model(self, runner: CliRunner, audio_file: str):
                result = runner.invoke(main, ["audio", "transcribe", audio_file, "--model", "whisper-1"])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

            def test_transcribe_temp(self, runner: CliRunner, audio_file: str):
                result = runner.invoke(main, ["audio", "transcribe", audio_file, "--temp", 1])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

            def test_transcribe_format(self, runner: CliRunner, audio_file: str):
                for fmt in RESPONSE_FORMAT_CHOICES:
                    result = runner.invoke(main, ["audio", "transcribe", audio_file, "--format", fmt])
                    assert result.exit_code == 0, result.stderr
                    assert result.stdout

            def test_transcribe_lang(self, runner: CliRunner, audio_file: str):
                result = runner.invoke(main, ["audio", "transcribe", audio_file, "--lang", "es"])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

        class Test_Translate:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["audio", "translate", "--help"])
                assert result.exit_code == 0, result.stderr

            def test_translate(self, runner: CliRunner, audio_file: str):
                result = runner.invoke(main, ["audio", "translate", audio_file])
                assert result.exit_code == 0, result.stderr
                assert result.stdout.lower() == "bruh\n"

            def test_translate_prompt(self, runner: CliRunner, audio_file: str):
                result = runner.invoke(main, ["audio", "transcribe", audio_file, "--prompt", "test"])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

            def test_translate_model(self, runner: CliRunner, audio_file: str):
                result = runner.invoke(main, ["audio", "transcribe", audio_file, "--model", "whisper-1"])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

            def test_translate_temp(self, runner: CliRunner, audio_file: str):
                result = runner.invoke(main, ["audio", "transcribe", audio_file, "--temp", 1])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

            def test_translate_format(self, runner: CliRunner, audio_file: str):
                for fmt in RESPONSE_FORMAT_CHOICES:
                    result = runner.invoke(main, ["audio", "transcribe", audio_file, "--format", fmt])
                    assert result.exit_code == 0, result.stderr
                    assert result.stdout

    class Test_Chat:
        def test_help(self, runner: CliRunner):
            result = runner.invoke(main, ["chat", "--help"])
            assert result.exit_code == 0, result.stderr

        def test_chat(self, runner: CliRunner):
            result = runner.invoke(main, ["chat", "respond with the word 'test'"])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

        def test_chat_model(self, runner: CliRunner):
            model_list = ["gpt-3.5-turbo"]
            for model in model_list:
                result = runner.invoke(main, ["chat", "respond with the word 'test'", "--model", model])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

        def test_chat_num(self, runner: CliRunner):
            result = runner.invoke(main, ["chat", "respond with the word 'test'", "--num", 2])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

        def test_chat_temp(self, runner: CliRunner):
            result = runner.invoke(main, ["chat", "respond with the word 'test'", "--temp", 2])
            assert result.exit_code == 0, result.stderr

        def test_chat_clearhistory(self, runner: CliRunner):
            result = runner.invoke(main, ["chat", "respond with the word 'test'", "--clearhistory"])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

            chat_history = load_chat()
            assert chat_history[0]["role"] == "user"
            assert chat_history[0]["content"] == "respond with the word 'test'\n"
            assert chat_history[1]["role"] == "assistant"
            assert chat_history[1]["content"]

        def test_chat_maxtokens(self, runner: CliRunner):
            result = runner.invoke(main, ["chat", "respond with the word 'test' repeated 10 times", "--maxtokens", 5])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

        def test_chat_stop(self, runner: CliRunner):
            result = runner.invoke(main, ["chat", "respond with the word 'test'", "--stop", "s"])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

        def test_chat_nostream(self, runner: CliRunner):
            result = runner.invoke(main, ["chat", "respond with the word 'test'", "--no-stream"])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

            result = runner.invoke(main, ["chat", "respond with the word 'test'", "--num", 2, "--no-stream"])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

    class Test_Complete:
        def test_help(self, runner: CliRunner):
            result = runner.invoke(main, ["complete", "--help"])
            assert result.exit_code == 0, result.stderr

        def test_complete(self, runner: CliRunner):
            result = runner.invoke(main, ["complete", "Gandalf: You shall not "])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

        def test_complete_model(self, runner: CliRunner):
            model_list = ["text-davinci-003", "text-davinci-002"]
            for model in model_list:
                result = runner.invoke(main, ["complete", "Gandalf: You shall not ", "--model", model])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

        def test_complete_num(self, runner: CliRunner):
            result = runner.invoke(main, ["complete", "Gandalf: You shall not ", "-mt", 1, "--num", 2])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

        def test_complete_temp(self, runner: CliRunner):
            result = runner.invoke(main, ["complete", "Gandalf: You shall not ", "--temp", 2])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

        def test_complete_maxtokens(self, runner: CliRunner):
            result = runner.invoke(main, ["complete", "test test test test test test test", "-mt", 1])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

        def test_complete_stop(self, runner: CliRunner):
            result = runner.invoke(main, ["complete", "Gandalf: You shall not ", "--stop", "s"])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

        def test_complete_nostream(self, runner: CliRunner):
            result = runner.invoke(main, ["complete", "Gandalf: You shall not ", "--no-stream"])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

            result = runner.invoke(main, ["complete", "Gandalf: You shall not ", "--num", 2, "--no-stream"])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

        def test_complete_echo(self, runner: CliRunner):
            result = runner.invoke(main, ["complete", "Gandalf: You shall not", "--echo"])
            assert result.exit_code == 0, result.stderr
            assert result.stdout.startswith("Gandalf: You shall not")

        def test_complete_suffix(self, runner: CliRunner):
            result = runner.invoke(main, ["complete", "Gandalf: You shall not", "--suffix", "Galdalf: Fly you fools"])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

    class Test_Config:
        def test_help(self, runner: CliRunner):
            result = runner.invoke(main, ["config", "--help"])
            assert result.exit_code == 0, result.stderr

        class Test_Path:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["config", "path", "--help"])
                assert result.exit_code == 0, result.stderr

            def test_path(self, runner: CliRunner):
                result = runner.invoke(main, ["config", "path"])
                assert result.exit_code == 0, result.stderr
                assert result.stdout == str(_CONFIG_FILE) + "\n"

        class Test_Set:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["config", "set", "--help"])
                assert result.exit_code == 0, result.stderr

            def test_set(self, runner: CliRunner):
                result = runner.invoke(main, ["config", "set", "chat", "context", "500"])
                assert result.exit_code == 0, result.stderr

                parser = ConfigParser()
                parser.read(_CONFIG_FILE)
                assert int(parser["chat"]["context"]) == 500

                result = runner.invoke(main, ["config", "set", "chat", "context", CONFIG["chat"]["context"]])
                assert result.exit_code == 0, result.stderr

                parser = ConfigParser()
                parser.read(_CONFIG_FILE)
                assert parser["chat"]["context"] == CONFIG["chat"]["context"]

        class Test_Show:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["config", "show", "--help"])
                assert result.exit_code == 0, result.stderr

            def test_show(self, runner: CliRunner):
                result = runner.invoke(main, ["config", "show"])
                assert result.exit_code == 0, result.stderr
                assert result.stdout == _CONFIG_FILE.read_text() + "\n"

    class Test_Edit:
        def test_help(self, runner: CliRunner):
            result = runner.invoke(main, ["edit", "--help"])
            assert result.exit_code == 0, result.stderr

        def test_edit(self, runner: CliRunner):
            result = runner.invoke(main, ["edit", "replate the word butts with tests", "I like big butts"])
            assert result.exit_code == 0, result.stderr
            assert result.stdout == "I like big tests\n\n"

        def test_edit_model(self, runner: CliRunner):
            model_list = ["text-davinci-edit-001", "code-davinci-edit-001"]
            for model in model_list:
                result = runner.invoke(main, ["edit", "replate the word butts with tests", "I like big butts", "--model", model])
                assert result.exit_code == 0, result.stderr
                assert result.stdout == "I like big tests\n\n"

        def test_edit_num(self, runner: CliRunner):
            result = runner.invoke(main, ["edit", "replate the word butts with tests", "I like big butts", "--num", 2])
            assert result.exit_code == 0, result.stderr
            assert result.stdout == "(0) I like big tests\n\n(1) I like big tests\n\n"

        def test_edit_temp(self, runner: CliRunner):
            result = runner.invoke(main, ["edit", "replate the word butts with tests", "I like big butts", "--temp", 0.1])
            assert result.exit_code == 0, result.stderr
            assert result.stdout == "I like big tests\n\n"

    class Test_File:
        def test_help(self, runner: CliRunner):
            result = runner.invoke(main, ["file", "--help"])
            assert result.exit_code == 0, result.stderr

        class Test_Delete:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["file", "delete", "--help"])
                assert result.exit_code == 0, result.stderr

        class Test_Download:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["file", "download", "--help"])
                assert result.exit_code == 0, result.stderr

        class Test_Find:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["file", "find", "--help"])
                assert result.exit_code == 0, result.stderr

        class Test_List:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["file", "list", "--help"])
                assert result.exit_code == 0, result.stderr

        class Test_Upload:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["file", "upload", "--help"])
                assert result.exit_code == 0, result.stderr

    class Test_Image:
        def test_help(self, runner: CliRunner):
            result = runner.invoke(main, ["image", "--help"])
            assert result.exit_code == 0, result.stderr

        class Test_Create:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["image", "create", "--help"])
                assert result.exit_code == 0, result.stderr

            def test_create(self, runner: CliRunner):
                result = runner.invoke(main, ["image", "create", "-p", "--size", "256x256", "a fat, black cat sitting in a garden"])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

            def test_create_num(self, runner: CliRunner):
                result = runner.invoke(main, ["image", "create", "-p",  "--size", "256x256", "a fat, black cat sitting in a garden", "--num", 2])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

            def test_create_size(self, runner: CliRunner):
                for size in SIZE_CHOICES:
                    result = runner.invoke(main, ["image", "create", "-p", "a fat, black cat sitting in a garden", "--size", size])
                    assert result.exit_code == 0, result.stderr
                    assert result.stdout

            def test_create_fmt(self, runner: CliRunner):
                for fmt in URL_CHOICES:
                    result = runner.invoke(main, ["image", "create", "-p",  "--size", "256x256", "a fat, black cat sitting in a garden", "--format", fmt])
                    assert result.exit_code == 0, result.stderr
                    assert result.stdout

        class Test_Edit:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["image", "edit", "--help"])
                assert result.exit_code == 0, result.stderr

            def test_edit(self, runner: CliRunner, image_file: str, mask_file: str):
                result = runner.invoke(main, ["image", "edit", "-p", "--size", "256x256", image_file, mask_file, "owl living in tree"])
                assert result.exit_code == 0, result.stderr

            def test_edit_num(self, runner: CliRunner, image_file: str, mask_file: str):
                result = runner.invoke(main, ["image", "edit", "-p",  "--size", "256x256", image_file, mask_file, "owl living in tree", "--num", 2])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

            def test_edit_size(self, runner: CliRunner, image_file: str, mask_file: str):
                for size in SIZE_CHOICES:
                    result = runner.invoke(main, ["image", "edit", "-p", image_file, mask_file, "owl living in tree", "--size", size])
                    assert result.exit_code == 0, result.stderr
                    assert result.stdout

            def test_edit_fmt(self, runner: CliRunner, image_file: str, mask_file: str):
                for fmt in URL_CHOICES:
                    result = runner.invoke(main, ["image", "edit", "-p",  "--size", "256x256", image_file, mask_file, "owl living in tree", "--format", fmt])
                    assert result.exit_code == 0, result.stderr
                    assert result.stdout

        class Test_Variation:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["image", "variation", "--help"])
                assert result.exit_code == 0, result.stderr

            def test_variation(self, runner: CliRunner, image_file: str):
                result = runner.invoke(main, ["image", "variation", "-p", "--size", "256x256", image_file])
                assert result.exit_code == 0, result.stderr

            def test_variation_num(self, runner: CliRunner, image_file: str):
                result = runner.invoke(main, ["image", "variation", "-p",  "--size", "256x256", image_file, "--num", 2])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

            def test_variation_size(self, runner: CliRunner, image_file: str):
                for size in SIZE_CHOICES:
                    result = runner.invoke(main, ["image", "variation", "-p", image_file, "--size", size])
                    assert result.exit_code == 0, result.stderr
                    assert result.stdout

            def test_variation_fmt(self, runner: CliRunner, image_file: str):
                for fmt in URL_CHOICES:
                    result = runner.invoke(main, ["image", "variation", "-p",  "--size", "256x256", image_file, "--format", fmt])
                    assert result.exit_code == 0, result.stderr
                    assert result.stdout

    class Test_Model:
        def test_help(self, runner: CliRunner):
            result = runner.invoke(main, ["model", "--help"])
            assert result.exit_code == 0, result.stderr

        class Test_List:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["model", "list", "--help"])
                assert result.exit_code == 0, result.stderr

            def test_list(self, runner: CliRunner):
                result = runner.invoke(main, ["model", "list"])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

        class Test_Show:
            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["model", "show", "--help"])
                assert result.exit_code == 0, result.stderr

            def test_show(self, runner: CliRunner):
                result = runner.invoke(main, ["model", "show", "ada"])
                assert result.exit_code == 0, result.stderr
                assert result.stdout

            def test_help(self, runner: CliRunner):
                result = runner.invoke(main, ["model", "show", "butts"])
                assert result.exit_code == 1

    class Test_Moderate:
        def test_help(self, runner: CliRunner):
            result = runner.invoke(main, ["moderate", "--help"])
            assert result.exit_code == 0, result.stderr

        def test_moderate(self, runner: CliRunner):
            result = runner.invoke(main, ["moderate", "lord of the rings is a bad movie"])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

    class Test_Prompt:
        @pytest.fixture(scope="class")
        def echo(self):
            def echo_func(prompt):
                print(prompt)

            return echo_func

        def test_prompt_arg(self, runner: CliRunner, echo):
            echo = click.command()(click.argument("prompt", type=utils.Prompt(), default="")(echo))
            result = runner.invoke(echo, ["test"])
            assert result.exit_code == 0, result.stderr
            assert result.stdout

        def test_prompt_pipe(self, runner: CliRunner, echo):
            echo = click.command()(click.argument("prompt", type=utils.Prompt(), default="")(echo))

            result = runner.invoke(echo, [], input="test")
            assert result.exit_code == 0, result.stderr
            assert result.stdout

        def test_prompt_arg_pipe(self, runner: CliRunner, echo):
            echo = click.command()(click.argument("prompt", type=utils.Prompt(), default="")(echo))
            result = runner.invoke(echo, ["test"], input="test")
            assert result.exit_code == 0, result.stderr
            assert result.stdout
