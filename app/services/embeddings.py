from sentence_transformers import SentenceTransformer


MODEL_NAME = "intfloat/multilingual-e5-small"


class EmbeddingServiceError(Exception):
    pass


class EmbeddingService:
    def __init__(self):
        self._model = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(MODEL_NAME)

        return self._model

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