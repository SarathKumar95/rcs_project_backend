
import unittest
from pathlib import Path
from dotenv import load_dotenv

from core.embeddings.embedding_service import EmbeddingService
from core.embeddings.gemini_provider import GeminiEmbeddingProvider


# Load .env from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


# Fake provider for unit tests
class FakeEmbeddingProvider:

    def embed(self, text):
        return [0.1] * 768


# Unit tests - No Gemini API calls
class TestEmbeddingService(unittest.TestCase):

    def setUp(self):
        self.emb_service = EmbeddingService(
            provider=FakeEmbeddingProvider()
        )

    def test_empty_query(self):
        with self.assertRaises(ValueError):
            self.emb_service.generate_query_embedding("")

    def test_empty_title_and_description(self):
        with self.assertRaises(ValueError):
            self.emb_service.generate_document_embedding("", "")

    def test_whitespace_query(self):
        with self.assertRaises(ValueError):
            self.emb_service.generate_query_embedding("   ")

    def test_whitespace_title_and_description(self):
        with self.assertRaises(ValueError):
            self.emb_service.generate_document_embedding("   ", "   ")


# Integration tests - Actual Gemini API calls
class TestGeminiIntegration(unittest.TestCase):

    def setUp(self):
        self.emb_service = EmbeddingService(
            provider=GeminiEmbeddingProvider()
        )

    def test_length_of_document_embedding(self):
        embedding = self.emb_service.generate_document_embedding(
            "Interstellar",
            "A team of astronauts travels through a wormhole."
        )

        self.assertEqual(len(embedding), 768)

    def test_length_of_query_embedding(self):
        embedding = self.emb_service.generate_query_embedding(
            "Movies about space exploration"
        )

        self.assertEqual(len(embedding), 768)


if __name__ == "__main__":
    unittest.main()
