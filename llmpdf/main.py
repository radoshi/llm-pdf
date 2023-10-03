from pathlib import Path
from typing import List
from urllib.parse import urlparse

import click
from rich.console import Console
from rich.progress import track
from rich.prompt import Confirm, Prompt

from llmpdf import __version__, util
from llmpdf.ai import ChatBot, Summarizer
from llmpdf.db import Database
from llmpdf.download import Arxiv

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


@main.command(name="list")
@click.option(
    "-c",
    "--collection",
    "collection_name",
    required=False,
    type=str,
    help="Name of the collection.",
)
def ls(collection_name: str):
    """Reset the collection."""
    database = Database()
    results = database.list(collection_name)
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
@click.argument("query", nargs=-1, type=str)
def arxiv(
    collection_name: str,
    query: List[str],
    dry_run: bool,
):
    """Download and index a paper from arxiv."""
    query_str = " ".join(query)

    downloader = Arxiv()
    database = Database()

    if query_str.startswith("http"):
        # If query_str is an arxiv url of the type http://arxiv.org/abs/2107.05580v1
        # or of the type http://arxiv.org/abs/quant-ph/0201082v1
        # extract an id which is the part of the URL after /abs/
        parsed_url = urlparse(query_str)
        if parsed_url.netloc == "arxiv.org" and parsed_url.path.startswith("/abs/"):
            arxiv_id = parsed_url.path.split("/abs/")[1]

            with console.status(f"Downloading {arxiv_id}..."):
                if not dry_run:
                    file_path = downloader.download(arxiv_id)
                else:
                    file_path = "dummy.pdf"

            with console.status(f"Indexing {file_path}..."):
                if not dry_run:
                    database.index(collection_name, file_path)
        else:
            console.print("Invalid arxiv URL.")
            return
    else:
        with console.status("[bold green]Searching arXiv..."):
            results = list(downloader.search(query_str))
        console.print(
            "\n".join([f"{idx}. {result.title}" for idx, result in enumerate(results)])
        )
        choices = list(str(i) for i in range(len(results)))
        choice = Prompt.ask("Choose a paper", choices=choices)
        result = results[int(choice)]

        with console.status(f"Downloading {result.title}..."):
            if not dry_run:
                file_path = result.download_pdf(dirpath=str(downloader.download_dir))
                console.print(f"Downloaded {file_path}")
            else:
                file_path = "dummy.pdf"

        with console.status(f"Indexing {file_path}..."):
            if not dry_run:
                database.index(collection_name, file_path)


@main.command()
@click.option(
    "-c",
    "--collection",
    "collection_name",
    type=str,
    required=True,
    help="Name of the collection.",
)
def chat(collection_name: str):
    """Chat with your PDFs."""
    console.print(f"Chatting with {collection_name}.")
    console.print("Type 'exit' to exit.")
    console.print("Type 'new' to start a new chat.")
    chatbot = ChatBot(collection_name)
    while True:
        query = Prompt.ask(
            "Question",
        )
        if query == "exit":
            return
        elif query == "new":
            console.print("Starting a new chat.")
            chatbot = ChatBot(collection_name)
            continue
        else:
            with console.status("[bold green] Asking 🤖..."):
                response, cost = chatbot.chat(query)
            console.print(response)
            console.print(f"Cost: ${cost:.2f}")
            console.print(f"Total Cost: ${chatbot.cost:.2f}")


@main.command()
@click.option(
    "-c",
    "--collection",
    "collection_name",
    type=str,
    required=True,
    help="Name of the collection.",
)
def summarize(collection_name: str):
    """Chat with your PDFs."""
    summarizer = Summarizer(collection_name=collection_name)
    if not Confirm.ask(
        f"Summarization will cost {sum(summarizer.estimate_tokens())} tokens and ${summarizer.calculate_cost():.2f}. Continue?",  # noqa: E501
        default=False,
    ):
        return

    # summary = summarizer.summarize()
    with console.status("[bold green]Summarizing..."):
        summary, cost = summarizer.summarize()

    console.print(summary)
    console.print(f"Cost: ${cost:.2f}")


if __name__ == "__main__":
    main()
