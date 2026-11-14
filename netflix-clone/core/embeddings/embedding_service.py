from functools import lru_cache
from typing import List, Optional

from core.embeddings.base import EmbeddingProvider
from core.embeddings.gemini_provider import GeminiEmbeddingProvider


class EmbeddingService:
    def __init__(self, provider: Optional[EmbeddingProvider] = None) -> None:
        self._provider = provider or GeminiEmbeddingProvider()

    def generate_document_embedding(
        self,
        title: str,
        description: Optional[str],
    ) -> List[float]:
        normalized_title = title.strip()
        normalized_description = (description or "").strip()
        if not normalized_title and not normalized_description:
            raise ValueError("A video title or description is required.")

        document = (
            f"title: {normalized_title or 'none'}"
            f" | text: {normalized_description}"
        )
        return self._provider.embed(document)

    def generate_query_embedding(self, query: str) -> List[float]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("Search query must not be empty.")

        formatted_query = f"task: search result | query: {normalized_query}"
        return self._provider.embed(formatted_query)


@lru_cache(maxsize=1)
def _default_service() -> EmbeddingService:
    return EmbeddingService()


def generate_document_embedding(
    title: str,
    description: Optional[str],
) -> List[float]:
    return _default_service().generate_document_embedding(title, description)


def generate_query_embedding(query: str) -> List[float]:
    return _default_service().generate_query_embedding(query)
