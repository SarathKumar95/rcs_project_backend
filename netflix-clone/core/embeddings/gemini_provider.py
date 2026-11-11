import os
from typing import List

from google import genai
from google.genai import types
from google.genai.errors import APIError

from .base import (
    EmbeddingConfigurationError,
    EmbeddingProvider,
    EmbeddingProviderError,
)


DEFAULT_MODEL = "gemini-embedding-2"
EMBEDDING_DIMENSIONS = 768


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or not api_key.strip():
            raise EmbeddingConfigurationError(
                "GEMINI_API_KEY is not set or is empty."
            )

        model = os.getenv("GEMINI_EMBEDDING_MODEL", DEFAULT_MODEL).strip()
        if not model:
            raise EmbeddingConfigurationError(
                "GEMINI_EMBEDDING_MODEL must not be empty."
            )

        dimensions_value = os.getenv(
            "GEMINI_EMBEDDING_DIMENSIONS",
            str(EMBEDDING_DIMENSIONS),
        )
        try:
            dimensions = int(dimensions_value)
        except ValueError as exc:
            raise EmbeddingConfigurationError(
                "GEMINI_EMBEDDING_DIMENSIONS must be an integer."
            ) from exc

        if dimensions != EMBEDDING_DIMENSIONS:
            raise EmbeddingConfigurationError(
                "GEMINI_EMBEDDING_DIMENSIONS must be 768."
            )

        self._model = model
        self._dimensions = dimensions
        self._client = genai.Client(api_key=api_key)

    def embed(self, text: str) -> List[float]:
        try:
            response = self._client.models.embed_content(
                model=self._model,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=self._dimensions,
                ),
            )
        except APIError as exc:
            raise EmbeddingProviderError(
                f"Gemini embedding request failed: {exc}"
            ) from exc

        if not response.embeddings or response.embeddings[0].values is None:
            raise EmbeddingProviderError(
                "Gemini returned no embedding values."
            )

        vector = [float(value) for value in response.embeddings[0].values]
        if len(vector) != EMBEDDING_DIMENSIONS:
            raise EmbeddingProviderError(
                "Gemini returned an embedding with "
                f"{len(vector)} dimensions; expected {EMBEDDING_DIMENSIONS}."
            )

        return vector
