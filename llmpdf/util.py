from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import List

BASE_DIR = Path("~/.llm-pdf").expanduser()
SETTINGS_FILE = BASE_DIR / "settings.env"
CHROMA_DIR = BASE_DIR / "chroma"

BASE_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE.touch(exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=SETTINGS_FILE)

    openai_api_key: str = ""
    model: str = "gpt-4"
    embedding_model: str = "text-embedding-ada-002"
    temperature: float = 0.0
    max_tokens: int = 500

    chroma_dir: Path = CHROMA_DIR
    base_dir: Path = BASE_DIR


def parse_pages(pages_str: str) -> List[str]:
    """Parse the pages string."""
    pages = []
    for page in pages_str.split(","):
        if "-" in page:
            start, end = page.split("-")
            pages.extend([str(i) for i in range(int(start), int(end) + 1)])
        else:
            pages.append(page)

    return pages
