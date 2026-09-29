from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from sqlalchemy import exists, func, inspect, select, text
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Note, NoteChunk
from app.services.chunking import chunk_text
from app.services.embeddings import embedding_service


ADVISORY_LOCK_ID = 7_341_942_247_895_661_441
DEFAULT_EMBEDDING_BATCH_SIZE = 64
EXPECTED_EMBEDDING_DIMENSION = NoteChunk.__table__.c.embedding.type.dim


class Embedder(Protocol):
    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding for each supplied passage."""


class BackfillError(RuntimeError):
    """Raised when the backfill cannot proceed safely."""


@dataclass
class BackfillReport:
    dry_run: bool
    notes_without_chunks: int = 0
    chunks_planned: int = 0
    null_embeddings: int = 0
    valid_embeddings_untouched: int = 0
    chunks_created: int = 0
    embeddings_generated: int = 0
    skipped_note_ids: list[int] = field(default_factory=list)
    suspicious_note_ids: list[int] = field(default_factory=list)


def _check_schema(db: Session) -> None:
    schema = inspect(db.connection())

    for table_name in ("notes", "note_chunks"):
        if not schema.has_table(table_name):
            raise BackfillError(
                f"Required table {table_name!r} does not exist"
            )

    chunk_columns = {
        column["name"]
        for column in schema.get_columns("note_chunks")
    }
    required_columns = {"note_id", "chunk_index", "content", "embedding"}
    missing_columns = required_columns - chunk_columns

    if missing_columns:
        names = ", ".join(sorted(missing_columns))
        raise BackfillError(
            f"note_chunks is missing required columns: {names}"
        )


def _acquire_advisory_lock(db: Session) -> None:
    acquired = db.execute(
        text("SELECT pg_try_advisory_xact_lock(:lock_id)"),
        {"lock_id": ADVISORY_LOCK_ID},
    ).scalar_one()

    if not acquired:
        raise BackfillError("Another RAG backfill is already running")


def _batched(values: Sequence[str], batch_size: int):
    for start in range(0, len(values), batch_size):
        yield list(values[start:start + batch_size])


def _validate_embeddings(
    texts: Sequence[str],
    embeddings: Sequence[Sequence[float]],
) -> list[list[float]]:
    if len(embeddings) != len(texts):
        raise BackfillError(
            "Embedding service returned a different number of vectors "
            "than input passages"
        )

    validated: list[list[float]] = []

    for embedding in embeddings:
        if len(embedding) != EXPECTED_EMBEDDING_DIMENSION:
            raise BackfillError(
                "Embedding service returned a vector with an unexpected "
                "dimension"
            )

        vector = [float(value) for value in embedding]

        if not all(math.isfinite(value) for value in vector):
            raise BackfillError(
                "Embedding service returned a non-finite vector value"
            )

        validated.append(vector)

    return validated


def _embed_texts(
    texts: Sequence[str],
    embedder: Embedder,
    batch_size: int,
) -> list[list[float]]:
    embeddings: list[list[float]] = []

    for batch in _batched(texts, batch_size):
        generated = embedder.embed_passages(batch)
        embeddings.extend(_validate_embeddings(batch, generated))

    return embeddings


def _find_missing_chunk_notes(db: Session, *, lock: bool) -> list[Note]:
    has_chunks = exists(
        select(NoteChunk.id).where(NoteChunk.note_id == Note.id)
    )
    statement = (
        select(Note)
        .where(~has_chunks)
        .order_by(Note.id)
    )

    if lock:
        statement = statement.with_for_update()

    return list(db.scalars(statement))


def _find_suspicious_notes(db: Session) -> list[int]:
    rows = db.execute(
        select(
            Note.id,
            Note.content,
            NoteChunk.chunk_index,
            NoteChunk.content,
        )
        .join(NoteChunk, NoteChunk.note_id == Note.id)
        .order_by(Note.id, NoteChunk.chunk_index, NoteChunk.id)
    ).all()

    notes: dict[int, tuple[str, list[tuple[int, str]]]] = {}

    for note_id, note_content, chunk_index, chunk_content in rows:
        if note_id not in notes:
            notes[note_id] = (note_content, [])
        notes[note_id][1].append((chunk_index, chunk_content))

    suspicious: list[int] = []

    for note_id, (note_content, actual_chunks) in notes.items():
        expected_chunks = list(enumerate(chunk_text(note_content)))

        if actual_chunks != expected_chunks:
            suspicious.append(note_id)

    return suspicious


def run_backfill(
    db: Session,
    *,
    dry_run: bool,
    embedder: Embedder,
    embedding_batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
) -> BackfillReport:
    if embedding_batch_size <= 0:
        raise ValueError("embedding_batch_size must be greater than 0")

    _check_schema(db)

    if not dry_run:
        _acquire_advisory_lock(db)

    missing_notes = _find_missing_chunk_notes(db, lock=not dry_run)
    null_embedding_count = db.scalar(
        select(func.count(NoteChunk.id)).where(
            NoteChunk.embedding.is_(None)
        )
    ) or 0
    valid_embedding_count = db.scalar(
        select(func.count(NoteChunk.id)).where(
            NoteChunk.embedding.is_not(None)
        )
    ) or 0

    chunks_by_note: list[tuple[Note, list[str]]] = []
    skipped_note_ids: list[int] = []

    for note in missing_notes:
        chunks = chunk_text(note.content)

        if chunks:
            chunks_by_note.append((note, chunks))
        else:
            skipped_note_ids.append(note.id)

    report = BackfillReport(
        dry_run=dry_run,
        notes_without_chunks=len(missing_notes),
        chunks_planned=sum(len(chunks) for _, chunks in chunks_by_note),
        null_embeddings=null_embedding_count,
        valid_embeddings_untouched=valid_embedding_count,
        skipped_note_ids=skipped_note_ids,
        suspicious_note_ids=_find_suspicious_notes(db),
    )

    if dry_run:
        return report

    for note, chunks in chunks_by_note:
        # Recheck after locking the note so concurrent backfill runs cannot
        # create a second chunk set.
        chunk_exists = db.scalar(
            select(
                exists().where(NoteChunk.note_id == note.id)
            )
        )

        if chunk_exists:
            continue

        embeddings = _embed_texts(
            chunks,
            embedder,
            embedding_batch_size,
        )

        for index, (content, embedding) in enumerate(
            zip(chunks, embeddings, strict=True)
        ):
            db.add(
                NoteChunk(
                    note_id=note.id,
                    chunk_index=index,
                    content=content,
                    embedding=embedding,
                )
            )
            report.chunks_created += 1
            report.embeddings_generated += 1

    db.flush()

    chunks_missing_embeddings = list(
        db.scalars(
            select(NoteChunk)
            .where(NoteChunk.embedding.is_(None))
            .order_by(NoteChunk.id)
            .with_for_update()
        )
    )

    for start in range(
        0,
        len(chunks_missing_embeddings),
        embedding_batch_size,
    ):
        chunk_batch = chunks_missing_embeddings[
            start:start + embedding_batch_size
        ]
        texts = [chunk.content for chunk in chunk_batch]
        embeddings = _embed_texts(
            texts,
            embedder,
            embedding_batch_size,
        )

        for chunk, embedding in zip(
            chunk_batch,
            embeddings,
            strict=True,
        ):
            chunk.embedding = embedding
            report.embeddings_generated += 1

    db.flush()

    return report


def execute_backfill(
    *,
    dry_run: bool,
    embedder: Embedder | None = None,
    session_factory: Callable[[], Session] = SessionLocal,
    embedding_batch_size: int = DEFAULT_EMBEDDING_BATCH_SIZE,
) -> BackfillReport:
    selected_embedder = embedder or embedding_service
    db = session_factory()

    try:
        report = run_backfill(
            db,
            dry_run=dry_run,
            embedder=selected_embedder,
            embedding_batch_size=embedding_batch_size,
        )

        if dry_run:
            db.rollback()
        else:
            db.commit()

        return report
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _print_report(report: BackfillReport) -> None:
    mode = "dry-run" if report.dry_run else "apply"
    print(f"mode={mode}")
    print(f"notes_without_chunks={report.notes_without_chunks}")
    print(f"chunks_planned={report.chunks_planned}")
    print(f"null_embeddings={report.null_embeddings}")
    print(
        "valid_embeddings_untouched="
        f"{report.valid_embeddings_untouched}"
    )
    print(f"chunks_created={report.chunks_created}")
    print(f"embeddings_generated={report.embeddings_generated}")
    print(f"skipped_note_ids={report.skipped_note_ids}")
    print(f"suspicious_note_ids={report.suspicious_note_ids}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Backfill missing RAG chunks and embeddings safely."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write and commit changes. Without this flag, only report them.",
    )
    parser.add_argument(
        "--embedding-batch-size",
        type=int,
        default=DEFAULT_EMBEDDING_BATCH_SIZE,
        help="Maximum number of passages embedded in one model call.",
    )
    args = parser.parse_args(argv)

    try:
        report = execute_backfill(
            dry_run=not args.apply,
            embedding_batch_size=args.embedding_batch_size,
        )
    except Exception as exc:
        print(
            f"Backfill failed ({type(exc).__name__}); transaction rolled back.",
            file=sys.stderr,
        )
        return 1

    _print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
