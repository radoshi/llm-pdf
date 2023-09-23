import sys
from pathlib import Path
from typing import Tuple

import click
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console

from llmpdf import __version__

BASEDIR = Path("~/.llm-pdf").expanduser()
SETTINGS_FILE = BASEDIR / "settings.env"
DB_FILE = BASEDIR / "db.sqlite"
EMBED_DIR = BASEDIR / "embeddings"


def create_config():
    BASEDIR.mkdir(parents=True, exist_ok=True)
    EMBED_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.touch(exist_ok=True)
    DB_FILE.touch(exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=SETTINGS_FILE)

    openai_api_key: str = ""
    model: str = "gpt-3.5-turbo"
    embedding_model: str = "text-embedding-ada-002"
    temperature: float = 0.1
    max_tokens: int = 1000


# def load_templates(path: Path) -> Optional[TemplateLibrary]:
#     path = path / "prompts"
#     if path.exists():
#         return TemplateLibrary.from_file_or_directory(path)
#     else:
#         return None


# def init_db(config_dir: Path):
#     config_dir.mkdir(parents=True, exist_ok=True)
#     db_path = config_dir / "db.sqlite"
#     _ = db.Database.get(db_path)


# def get_cached_response(settings: Settings, messages: list[dict]) -> Optional[Message]:
#     record = db.get_last_inserted_row()
#     if not record:
#         return None
#     if (
#         record.model != settings.model
#         or record.temperature != settings.temperature
#         or record.max_tokens != settings.max_tokens
#         or record.system_message != messages[0]["content"]
#         or record.user_message != messages[1]["content"]
#     ):
#         return None

#     return Message(
#         role="assistant",
#         content=record.assistant_message,
#     )


# def get_code(inputs) -> str:
#     files = [f for input in inputs for f in Path.cwd().glob(input)]
#     file_name = [f.name for f in files]
#     file_texts = [f.read_text() for f in files]
#     file_blobs = [
#         f"FILENAME: {name}\n```{text}\n```"
#         for (name, text) in zip(file_name, file_texts)
#     ]
#     return "\n---\n".join(file_blobs)


# def get_max_tokens(message: str) -> int:
#     return len(message.split(" "))


@click.command()
@click.option("-v", "--version", is_flag=True, help="Show version.")
@click.option("-4", "--gpt-4", is_flag=True, help="Use GPT-4.")
@click.argument("instructions", nargs=-1)
def main(
    gpt_4: bool,
    version: bool,
    instructions: Tuple[str, ...],
):
    """Chat with your PDFs."""
    console = Console()

    create_config()

    if version:
        console.print(f"[bold green]llm-pdf[/] version {__version__}")
        sys.exit(0)

    settings = Settings()
    if not settings.openai_api_key:
        openai_api_key = click.prompt("Please enter your OpenAI API key", type=str)
        settings.openai_api_key = openai_api_key
        # Append OPENAI_API_KEY to settings file
        with SETTINGS_FILE.open("a") as f:
            f.write(f"OPENAI_API_KEY={openai_api_key}\n")

    if gpt_4:
        settings.model = "gpt-4"

    # init_db(settings.config_dir)

    # if not instructions:
    #     raise click.UsageError("Please provide some instructions.")

    # library = load_templates(settings.config_dir) or load_templates(
    #     Path(__file__).parent.parent
    # )
    # if not library:
    #     raise click.UsageError("No templates found.")

    # if inputs:
    #     code = get_code(inputs)
    #     message = library["coding/input"].message(
    #         code=code, instructions=" ".join(instructions)
    #     )
    # else:
    #     message = library["coding/simple"].message(instructions=" ".join(instructions))

    # messages = [library["coding/system"].message(), message]

    # cached_response = get_cached_response(settings, messages)
    # if no_cache or not cached_response:
    #     with console.status("[bold green]Asking OpenAI..."):
    #         response = openai.ChatCompletion.create(
    #             api_key=settings.openai_api_key,
    #             model=settings.model,
    #             temperature=settings.temperature,
    #             max_tokens=settings.max_tokens,
    #             messages=messages,
    #         )

    #     message = Message.from_message(response.choices[0]["message"])  # type: ignore

    #     db.write(
    #         model=settings.model,
    #         temperature=settings.temperature,
    #         max_tokens=settings.max_tokens,
    #         system_message=messages[0]["content"],
    #         user_message=messages[1]["content"],
    #         assistant_message=message.content,
    #         input_tokens=response.usage["prompt_tokens"],  # type: ignore
    #         output_tokens=response.usage["completion_tokens"],  # type: ignore
    #     )
    # else:
    #     message = cached_response

    # code_block = message.code()
    # if code_block:
    #     console.print(Syntax(code_block.code, code_block.lang, word_wrap=True))
    #     if clipboard:
    #         pyperclip.copy(code_block.code)
    # else:
    #     console.print(f"No code found in message: \n\n{message.content}")
    #     sys.exit(1)


if __name__ == "__main__":
    main()
