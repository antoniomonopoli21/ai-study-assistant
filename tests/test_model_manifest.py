from app.config import settings
from app.model_manifest import model_manifest


def test_runtime_model_config_matches_manifest():
    assert (
        settings.embedding_model
        == model_manifest.embedding.model
    )

    assert (
        settings.embedding_model_revision
        == model_manifest.embedding.revision
    )

    assert (
        settings.reranker_model
        == model_manifest.reranker.model
    )

    assert (
        settings.reranker_model_revision
        == model_manifest.reranker.revision
    )