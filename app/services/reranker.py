import logging
import math
from threading import Lock

from sentence_transformers import CrossEncoder

from app.config import settings
from app.models import NoteChunk


logger = logging.getLogger(__name__)


class RerankerServiceError(Exception):
    pass


class RerankerService:
    def __init__(self):
        self._model: CrossEncoder | None = None

        self._model_lock = Lock()
        self._predict_lock = Lock()

    def _get_model(self) -> CrossEncoder:
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    self._model = CrossEncoder(
                        settings.reranker_model,
                        revision=settings.reranker_model_revision,
                    )

        return self._model

    def load_model(self) -> None:
        try:
            self._get_model()
        except Exception as exc:
            logger.exception(
                "Reranker model loading failed"
            )

            raise RerankerServiceError(
                "Reranker model loading failed"
            ) from exc

    def is_ready(self) -> bool:
        return self._model is not None


    def rerank(
        self,
        query: str,
        candidates: list[tuple[NoteChunk, float]],
    ) -> list[tuple[NoteChunk, float, float]]:
        if not candidates:
            return []

        pairs = [
            (
                query,
                chunk.content,
            )
            for chunk, distance in candidates
        ]

        try:
            model = self._get_model()

            with self._predict_lock:
                raw_scores = model.predict(pairs)

            if len(raw_scores) != len(candidates):
                raise ValueError(
                    "Reranker score count does not match "
                    "candidate count"
                )

            scores = [
                float(score)
                for score in raw_scores
            ]

            if not all(
                math.isfinite(score)
                for score in scores
            ):
                raise ValueError(
                    "Reranker returned a non-finite score"
                )

            reranked_results = [
                (
                    chunk,
                    distance,
                    score,
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
            logger.exception(
                "Reranker inference failed"
            )

            raise RerankerServiceError(
                "Reranker inference failed"
            ) from exc


reranker_service = RerankerService()