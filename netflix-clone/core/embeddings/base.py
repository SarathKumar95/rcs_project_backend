from abc import ABC, abstractmethod
from typing import List


class EmbeddingError(RuntimeError):
    """Base exception for embedding generation errors."""


class EmbeddingConfigurationError(EmbeddingError):
    """Raised when embedding provider configuration is invalid."""


class EmbeddingProviderError(EmbeddingError):
    """Raised when an embedding provider cannot generate a valid vector."""


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate an embedding for the supplied text."""
