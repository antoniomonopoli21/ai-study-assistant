from types import SimpleNamespace

import pytest

from app.services.reranker import (
    RerankerService,
    RerankerServiceError,
)


class FakeModel:
    def __init__(self, scores):
        self.scores = scores

    def predict(self, pairs):
        return self.scores


def make_chunk(
    note_id: int,
    content: str,
):
    return SimpleNamespace(
        note_id=note_id,
        chunk_index=0,
        content=content,
    )


def test_reranker_returns_empty_list_for_no_candidates():
    service = RerankerService()

    result = service.rerank(
        query="question",
        candidates=[],
    )

    assert result == []


def test_reranker_orders_candidates_by_score(
    monkeypatch,
):
    service = RerankerService()

    monkeypatch.setattr(
        service,
        "_get_model",
        lambda: FakeModel(
            [-2.0, 5.0]
        ),
    )

    first_chunk = make_chunk(
        1,
        "First",
    )

    second_chunk = make_chunk(
        2,
        "Second",
    )

    result = service.rerank(
        query="question",
        candidates=[
            (first_chunk, 0.10),
            (second_chunk, 0.20),
        ],
    )

    assert result[0][0] is second_chunk
    assert result[0][2] == 5.0

    assert result[1][0] is first_chunk
    assert result[1][2] == -2.0


def test_reranker_rejects_wrong_score_count(
    monkeypatch,
):
    service = RerankerService()

    monkeypatch.setattr(
        service,
        "_get_model",
        lambda: FakeModel(
            [1.0]
        ),
    )

    candidates = [
        (
            make_chunk(1, "First"),
            0.10,
        ),
        (
            make_chunk(2, "Second"),
            0.20,
        ),
    ]

    with pytest.raises(
        RerankerServiceError
    ):
        service.rerank(
            query="question",
            candidates=candidates,
        )


@pytest.mark.parametrize(
    "invalid_score",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_reranker_rejects_non_finite_scores(
    monkeypatch,
    invalid_score,
):
    service = RerankerService()

    monkeypatch.setattr(
        service,
        "_get_model",
        lambda: FakeModel(
            [invalid_score]
        ),
    )

    with pytest.raises(
        RerankerServiceError
    ):
        service.rerank(
            query="question",
            candidates=[
                (
                    make_chunk(
                        1,
                        "Context",
                    ),
                    0.10,
                )
            ],
        )