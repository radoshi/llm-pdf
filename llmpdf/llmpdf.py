from pathlib import Path
from typing import List

import click
from rich.console import Console
from rich.progress import track
from rich.prompt import Confirm

from llmpdf import __version__, util
from llmpdf.db import Database

settings = util.Settings()
console = Console()


def expand_globs(pdfs: list[str]) -> list[str]:
    files = []
    for pdf in pdfs:
        pdf = Path(pdf).expanduser()
        if "*" in pdf.name:
            files.extend(Path.cwd().glob(pdf.name))
        else:
            files.append(pdf)

    files = [str(Path(file).resolve()) for file in files if Path(file).is_file()]

    return files


@click.group()
@click.option("-4", "--gpt-4", is_flag=True, default=False, help="Use GPT-4.")
@click.version_option(__version__)
def main(gpt_4: bool):
    pass


@main.command()
@click.option(
    "-c",
    "--collection",
    "collection_name",
    required=False,
    type=str,
    help="Name of the collection.",
)
def list(collection_name: str):
    """Reset the collection."""
    database = Database()
    results = database.list_(collection_name)
    console.print(results)


@main.command()
@click.option(
    "-c",
    "--collection",
    "collection_name",
    type=str,
    required=True,
    help="Name of the collection.",
)
def delete(collection_name: str):
    """Reset the collection."""
    if not Confirm.ask(
        f"Are you sure you want to delete {collection_name}?", default=False
    ):
        return

    database = Database()
    database.delete(collection_name)

    console.print(f"Deleted {collection_name}.")


@main.command()
@click.option(
    "-c",
    "--collection",
    "collection_name",
    type=str,
    required=True,
    help="Name of the collection.",
)
@click.option("-n", "--dry-run", is_flag=True, default=False, help="Dry run.")
@click.argument("pdfs", nargs=-1, type=click.Path(exists=True))
def index(
    collection_name: str,
    pdfs: List[str],
    dry_run: bool = False,
):
    """Chat with your PDFs."""

    database = Database()

    pdfs = expand_globs(pdfs)
    console.print(f"Indexing PDFs {pdfs}")

    for pdf in track(pdfs):
        if not dry_run:
            database.index(collection_name, pdf)


if __name__ == "__main__":
    main()
