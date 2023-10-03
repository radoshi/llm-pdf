from typing import Generator

import arxiv

from llmpdf.util import Settings

settings = Settings()


class Arxiv:
    """Download papers from arXiv"""

    def __init__(self):
        self.download_dir = settings.base_dir / "arxiv"
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def search(self, query: str) -> Generator[arxiv.Result, None, None]:
        """Search arXiv"""
        self.query = query
        search = arxiv.Search(query=query, max_results=10)
        return search.results()

    def download(self, id: str):
        """Download a single paperfrom arXiv"""
        search = arxiv.Search(id_list=[id])
        result = next(search.results())
        if result:
            return result.download_pdf(dirpath=str(self.download_dir))
        else:
            raise ValueError(f"Could not find paper with id {id}")

    def download_url(self, url: str):
        """Download a single paperfrom arXiv"""
        paper = next(self.search(url))
        if paper:
            print(f"Downloading {paper.title}...")
