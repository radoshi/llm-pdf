from typing import List

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from pydantic import BaseModel
from pypdf import PdfReader

from llmpdf import util


class Result(BaseModel):
    """A search result."""

    document: str
    page: str


class Database:
    """Wraps the SQLite and Vector Databases."""

    embedding_model = "text-embedding-ada-002"

    def __init__(self):
        """Initialize the database."""
        settings = util.Settings()
        chroma_dir = settings.chroma_dir
        self.db_client = chromadb.PersistentClient(
            path=str(chroma_dir), settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=self.embedding_model,
        )

    def _get_collection(self, collection_name: str) -> chromadb.Collection:
        """Get the collection."""
        return self.db_client.get_collection(
            collection_name, embedding_function=self.embedding_fn
        )

    def get_pages(self, collection_name: str, pages: List[str]) -> List[str]:
        """Get pages by page number."""
        coll = self._get_collection(collection_name)
        result = coll.get(ids=pages)
        return result["documents"] or []

    def index(self, collection_name: str, pdf: str):
        """Index PDFs."""
        coll = self.db_client.get_or_create_collection(
            collection_name, embedding_function=self.embedding_fn
        )
        reader = PdfReader(pdf)

        for page in reader.pages:
            id = page.page_number
            text = page.extract_text() + " "
            metadata = {"page": str(id)}

            coll.add(documents=text, ids=str(id), metadatas=metadata)

    def search(self, collection_name: str, query: str) -> List[Result]:
        """Search the database."""
        coll = self._get_collection(collection_name)
        res = coll.query(query_texts=query, n_results=3)
        documents = res["documents"][0] if res["documents"] else []
        metadatas = res["metadatas"][0] if res["metadatas"] else []
        results = [
            Result(document=document, page=str(metadata["page"]))
            for (document, metadata) in zip(documents, metadatas)
        ]
        return results

    def delete(self, collection_name: str):
        """Reset the database."""
        try:
            self.db_client.delete_collection(collection_name)
        except ValueError:
            pass

    def list(self, collection_name: str | None = None, limit: int = 5) -> list[str]:
        """List collections or documents in the collection."""
        if collection_name is None:
            collections = self.db_client.list_collections()
            return [c.name for c in collections]
        else:
            coll = self._get_collection(collection_name)
            return coll.peek(limit=limit)["documents"] or []

    def count(self, collection_name: str):
        """Count the number of documents in the collection."""
        coll = self._get_collection(collection_name)
        return coll.count()
