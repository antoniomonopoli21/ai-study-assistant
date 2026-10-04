import app.services.embeddings as embeddings_module
import app.services.reranker as reranker_module

from app.config import settings
from app.services.embeddings import EmbeddingService
from app.services.reranker import RerankerService


def test_embedding_model_uses_pinned_revision(
    monkeypatch,
):
    captured = {}

    class FakeSentenceTransformer:
        def __init__(
            self,
            model_name,
            **kwargs,
        ):
            captured["model_name"] = model_name
            captured["revision"] = kwargs.get(
                "revision"
            )

        def get_sentence_embedding_dimension(
            self,
        ):
            return 384

    monkeypatch.setattr(
        embeddings_module,
        "SentenceTransformer",
        FakeSentenceTransformer,
    )

    service = EmbeddingService()
    service.load_model()

    assert (
        captured["model_name"]
        == settings.embedding_model
    )

    assert (
        captured["revision"]
        == settings.embedding_model_revision
    )


def test_reranker_model_uses_pinned_revision(
    monkeypatch,
):
    captured = {}

    class FakeCrossEncoder:
        def __init__(
            self,
            model_name,
            **kwargs,
        ):
            captured["model_name"] = model_name
            captured["revision"] = kwargs.get(
                "revision"
            )

    monkeypatch.setattr(
        reranker_module,
        "CrossEncoder",
        FakeCrossEncoder,
    )

    service = RerankerService()
    service.load_model()

    assert (
        captured["model_name"]
        == settings.reranker_model
    )

    assert (
        captured["revision"]
        == settings.reranker_model_revision
    )