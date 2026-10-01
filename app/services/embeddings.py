from threading import Lock

from sentence_transformers import SentenceTransformer

from app.config import settings


EMBEDDING_DIMENSION = 384


class EmbeddingServiceError(Exception):
    pass


class EmbeddingService:
    def __init__(self):
        self._model: SentenceTransformer | None = None
        self._model_lock = Lock()

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    model = SentenceTransformer(
                        settings.embedding_model
                    )

                    dimension = (
                        model.get_sentence_embedding_dimension()
                    )

                    if dimension != EMBEDDING_DIMENSION:
                        raise ValueError(
                            "Embedding model dimension "
                            f"must be {EMBEDDING_DIMENSION}, "
                            f"got {dimension}"
                        )

                    self._model = model

        return self._model

    def load_model(self) -> None:
        try:
            self._get_model()
        except Exception as exc:
            raise EmbeddingServiceError(
                "Embedding model loading failed"
            ) from exc

    def is_ready(self) -> bool:
        return self._model is not None

    def embed_passages(
        self,
        texts: list[str]
    ) -> list[list[float]]:
        if not texts:
            return []

        try:
            model = self._get_model()

            inputs = [
                f"passage: {text}"
                for text in texts
            ]

            embeddings = model.encode(
                inputs,
                normalize_embeddings=True
            )

            return embeddings.tolist()

        except Exception as exc:
            raise EmbeddingServiceError(
                "Embedding generation failed"
            ) from exc

    def embed_query(
        self,
        text: str
    ) -> list[float]:
        try:
            model = self._get_model()

            embedding = model.encode(
                f"query: {text}",
                normalize_embeddings=True
            )

            return embedding.tolist()

        except Exception as exc:
            raise EmbeddingServiceError(
                "Embedding generation failed"
            ) from exc


embedding_service = EmbeddingService()