import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Note, NoteChunk, User
from app.services.chunking import chunk_text
from scripts.backfill_rag import (
    ADVISORY_LOCK_ID,
    BackfillError,
    execute_backfill,
)


VECTOR_DIMENSION = NoteChunk.__table__.c.embedding.type.dim

BackfillSession = sessionmaker(
    bind=create_engine(settings.test_database_url),
    autoflush=False,
    autocommit=False,
)


class FakeEmbedder:
    def __init__(
        self,
        *,
        fail_on_call: int | None = None,
        dimension: int = VECTOR_DIMENSION,
        omit_last: bool = False,
    ):
        self.calls: list[list[str]] = []
        self.fail_on_call = fail_on_call
        self.dimension = dimension
        self.omit_last = omit_last

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))

        if self.fail_on_call == len(self.calls):
            raise RuntimeError("deterministic embedding failure")

        embeddings = [
            [float(len(text))] + [0.0] * (self.dimension - 1)
            for text in texts
        ]

        if self.omit_last:
            return embeddings[:-1]

        return embeddings


def _create_user_and_note(
    *,
    email: str,
    content: str,
) -> tuple[int, int]:
    with BackfillSession.begin() as db:
        user = User(
            email=email,
            hashed_password="not-used-by-backfill-tests",
        )
        db.add(user)
        db.flush()

        note = Note(
            user_id=user.id,
            subject="Backfill",
            title="Legacy note",
            content=content,
            priority=1,
        )
        db.add(note)
        db.flush()

        return user.id, note.id


def _chunks_for_note(note_id: int) -> list[NoteChunk]:
    with BackfillSession() as db:
        return list(
            db.scalars(
                select(NoteChunk)
                .where(NoteChunk.note_id == note_id)
                .order_by(NoteChunk.chunk_index)
            )
        )


def test_dry_run_does_not_write_or_embed(client):
    _, note_id = _create_user_and_note(
        email="dry-run@example.com",
        content="one two three",
    )
    embedder = FakeEmbedder()

    report = execute_backfill(
        dry_run=True,
        embedder=embedder,
        session_factory=BackfillSession,
    )

    assert report.notes_without_chunks == 1
    assert report.chunks_planned == 1
    assert report.chunks_created == 0
    assert report.embeddings_generated == 0
    assert embedder.calls == []
    assert _chunks_for_note(note_id) == []


def test_apply_creates_every_chunk_and_is_idempotent(client):
    content = " ".join(f"word-{index}" for index in range(250))
    user_id, note_id = _create_user_and_note(
        email="idempotent@example.com",
        content=content,
    )
    embedder = FakeEmbedder()

    first_report = execute_backfill(
        dry_run=False,
        embedder=embedder,
        session_factory=BackfillSession,
    )
    calls_after_first_run = len(embedder.calls)

    second_report = execute_backfill(
        dry_run=False,
        embedder=embedder,
        session_factory=BackfillSession,
    )

    chunks = _chunks_for_note(note_id)
    expected_chunks = chunk_text(content)

    assert first_report.chunks_created == len(expected_chunks) == 3
    assert first_report.embeddings_generated == 3
    assert second_report.notes_without_chunks == 0
    assert second_report.null_embeddings == 0
    assert second_report.chunks_created == 0
    assert second_report.embeddings_generated == 0
    assert len(embedder.calls) == calls_after_first_run
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert [chunk.content for chunk in chunks] == expected_chunks
    assert all(len(chunk.embedding) == VECTOR_DIMENSION for chunk in chunks)

    with BackfillSession() as db:
        note = db.get(Note, note_id)
        assert note is not None
        assert note.user_id == user_id
        assert note.content == content


def test_apply_fills_only_missing_embeddings(client):
    _, note_id = _create_user_and_note(
        email="null-embedding@example.com",
        content="first chunk second chunk",
    )
    valid_embedding = [0.25] * VECTOR_DIMENSION

    with BackfillSession.begin() as db:
        db.add_all([
            NoteChunk(
                note_id=note_id,
                chunk_index=0,
                content="first chunk",
                embedding=None,
            ),
            NoteChunk(
                note_id=note_id,
                chunk_index=1,
                content="second chunk",
                embedding=valid_embedding,
            ),
        ])

    embedder = FakeEmbedder()
    report = execute_backfill(
        dry_run=False,
        embedder=embedder,
        session_factory=BackfillSession,
    )
    chunks = _chunks_for_note(note_id)

    assert report.null_embeddings == 1
    assert report.chunks_created == 0
    assert report.embeddings_generated == 1
    assert embedder.calls == [["first chunk"]]
    assert chunks[0].content == "first chunk"
    assert chunks[0].embedding is not None
    assert chunks[1].content == "second chunk"
    assert list(chunks[1].embedding) == pytest.approx(valid_embedding)


def test_failure_rolls_back_all_changes(client):
    _, new_note_id = _create_user_and_note(
        email="rollback-new@example.com",
        content="new note needs chunks",
    )
    _, existing_note_id = _create_user_and_note(
        email="rollback-existing@example.com",
        content="existing chunk",
    )

    with BackfillSession.begin() as db:
        db.add(
            NoteChunk(
                note_id=existing_note_id,
                chunk_index=0,
                content="existing chunk",
                embedding=None,
            )
        )

    embedder = FakeEmbedder(fail_on_call=2)

    with pytest.raises(RuntimeError, match="deterministic embedding failure"):
        execute_backfill(
            dry_run=False,
            embedder=embedder,
            session_factory=BackfillSession,
        )

    assert _chunks_for_note(new_note_id) == []
    existing_chunks = _chunks_for_note(existing_note_id)
    assert len(existing_chunks) == 1
    assert existing_chunks[0].embedding is None


def test_invalid_embedding_dimension_rolls_back(client):
    _, note_id = _create_user_and_note(
        email="dimension@example.com",
        content="dimension mismatch",
    )

    with pytest.raises(BackfillError, match="unexpected dimension"):
        execute_backfill(
            dry_run=False,
            embedder=FakeEmbedder(dimension=VECTOR_DIMENSION - 1),
            session_factory=BackfillSession,
        )

    assert _chunks_for_note(note_id) == []


def test_invalid_embedding_count_rolls_back(client):
    _, note_id = _create_user_and_note(
        email="count@example.com",
        content="embedding count mismatch",
    )

    with pytest.raises(BackfillError, match="different number of vectors"):
        execute_backfill(
            dry_run=False,
            embedder=FakeEmbedder(omit_last=True),
            session_factory=BackfillSession,
        )

    assert _chunks_for_note(note_id) == []


def test_apply_refuses_to_run_when_advisory_lock_is_held(client):
    _, note_id = _create_user_and_note(
        email="lock@example.com",
        content="wait for the other backfill",
    )
    embedder = FakeEmbedder()

    with BackfillSession() as lock_db:
        lock_db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_id)"),
            {"lock_id": ADVISORY_LOCK_ID},
        )

        with pytest.raises(BackfillError, match="already running"):
            execute_backfill(
                dry_run=False,
                embedder=embedder,
                session_factory=BackfillSession,
            )

        lock_db.rollback()

    assert embedder.calls == []
    assert _chunks_for_note(note_id) == []


def test_blank_notes_are_skipped_and_partial_sets_are_preserved(client):
    _, blank_note_id = _create_user_and_note(
        email="blank@example.com",
        content="   ",
    )
    partial_content = " ".join(
        f"partial-{index}"
        for index in range(250)
    )
    _, partial_note_id = _create_user_and_note(
        email="partial@example.com",
        content=partial_content,
    )
    expected = chunk_text(partial_content)
    valid_embedding = [0.5] * VECTOR_DIMENSION

    with BackfillSession.begin() as db:
        db.add(
            NoteChunk(
                note_id=partial_note_id,
                chunk_index=2,
                content=expected[2],
                embedding=valid_embedding,
            )
        )

    embedder = FakeEmbedder()
    report = execute_backfill(
        dry_run=False,
        embedder=embedder,
        session_factory=BackfillSession,
    )

    assert report.skipped_note_ids == [blank_note_id]
    assert report.suspicious_note_ids == [partial_note_id]
    assert _chunks_for_note(blank_note_id) == []

    partial_chunks = _chunks_for_note(partial_note_id)
    assert len(partial_chunks) == 1
    assert partial_chunks[0].chunk_index == 2
    assert partial_chunks[0].content == expected[2]
    assert list(partial_chunks[0].embedding) == pytest.approx(valid_embedding)
    assert embedder.calls == []
