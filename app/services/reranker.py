from sentence_transformers import CrossEncoder

from app.config import settings
from app.models import NoteChunk


class RerankerServiceError(Exception):
    pass


class RerankerService:
    def __init__(self):
        self._model = None

    def _get_model(self) -> CrossEncoder:
        if self._model is None:
            self._model = CrossEncoder(
                settings.reranker_model
            )

        return self._model

    def rerank(
        self,
        query: str,
        candidates: list[tuple[NoteChunk, float]],
    ) -> list[tuple[NoteChunk, float, float]]:
        if not candidates:
            return []

        try:
            model = self._get_model()

            pairs = [
                (
                    query,
                    chunk.content,
                )
                for chunk, distance in candidates
            ]

            scores = model.predict(pairs)

            reranked_results = [
                (
                    chunk,
                    distance,
                    float(score),
                )
                for (
                    chunk,
                    distance,
                ), score in zip(
                    candidates,
                    scores,
                    strict=True,
                )
            ]

            reranked_results.sort(
                key=lambda item: item[2],
                reverse=True,
            )

            return reranked_results

        except Exception as exc:
            raise RerankerServiceError(
                "Reranker inference failed"
            ) from exc


reranker_service = RerankerService()