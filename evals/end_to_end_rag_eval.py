from uuid import uuid4

from sqlalchemy.engine import make_url

from app.config import settings
from app.database import SessionLocal
from app.models import Note, User
from app.routers.ask import ask_question
from app.schemas import AskRequest
from app.services.note_chunks import replace_note_chunks
from app.services.llm import llm_service

from evals.answer_dataset import ANSWER_EVAL_CASES
from evals.answer_judge_eval import (
    JUDGE_INSTRUCTIONS,
    build_judge_prompt,
    parse_judge_response,
)
from evals.retrieval_dataset import DOCUMENTS


EVAL_REQUEST_LIMIT = 3


def ensure_safe_eval_database() -> None:
    url = make_url(
        settings.database_url
    )

    allowed_hosts = {
        None,
        "localhost",
        "127.0.0.1",
    }

    if url.host not in allowed_hosts:
        raise RuntimeError(
            "End-to-end evaluation is only allowed "
            "against a local development database"
        )


def create_eval_data(db):
    eval_user = User(
        email=(
            f"rag-eval-{uuid4().hex}"
            "@example.com"
        ),
        hashed_password="not-used-by-eval",
    )

    db.add(eval_user)
    db.flush()

    note_id_to_document_id = {}

    for document in DOCUMENTS:
        note = Note(
            subject="RAG Evaluation",
            title=document["id"],
            content=document["text"],
            priority=1,
            user_id=eval_user.id,
        )

        db.add(note)

        # We need the database-generated note ID
        # before creating its chunks.
        db.flush()

        replace_note_chunks(
            db=db,
            note_id=note.id,
            content=note.content,
        )

        note_id_to_document_id[
            note.id
        ] = document["id"]

    # SessionLocal has autoflush=False, so make sure
    # every pending NoteChunk is visible to the SQL
    # retrieval queries that follow.
    db.flush()

    return (
        eval_user,
        note_id_to_document_id,
    )


def evaluate():
    ensure_safe_eval_database()

    db = SessionLocal()

    try:
        print(
            "=== End-to-End RAG Evaluation ==="
        )
        print(
            f"LLM model: "
            f"{settings.openai_model}"
        )
        print(
            f"Reranker model: "
            f"{settings.reranker_model}"
        )
        print(
            f"Reranker threshold: "
            f"{settings.reranker_threshold}"
        )
        print(
            f"Candidate K: "
            f"{settings.reranker_candidate_k}"
        )
        print(
            f"Request limit: "
            f"{EVAL_REQUEST_LIMIT}"
        )

        print()
        print(
            "Creating temporary evaluation data..."
        )

        (
            eval_user,
            note_id_to_document_id,
        ) = create_eval_data(db)

        total_cases = len(
            ANSWER_EVAL_CASES
        )

        answerable_cases = 0
        expected_source_hits = 0

        no_answer_cases = 0
        pre_llm_rejections = 0

        correct_count = 0
        grounded_count = 0
        complete_count = 0
        abstention_count = 0

        judge_pass_count = 0
        end_to_end_pass_count = 0

        for case in ANSWER_EVAL_CASES:
            expected_no_answer = (
                case["expected_no_answer"]
            )

            request = AskRequest(
                question=case["question"],
                limit=EVAL_REQUEST_LIMIT,
            )

            response = ask_question(
                request=request,
                db=db,
                current_user=eval_user,
            )

            selected_document_ids = [
                note_id_to_document_id[
                    source.note_id
                ]
                for source in response.sources
            ]

            context = "\n\n".join(
                source.content
                for source in response.sources
            )

            if expected_no_answer:
                no_answer_cases += 1

                if not response.sources:
                    pre_llm_rejections += 1

                source_requirement_passed = True

            else:
                answerable_cases += 1

                expected_context_ids = set(
                    case["context_ids"]
                )

                selected_id_set = set(
                    selected_document_ids
                )

                source_requirement_passed = bool(
                    expected_context_ids
                    & selected_id_set
                )

                if source_requirement_passed:
                    expected_source_hits += 1

            judge_prompt = build_judge_prompt(
                question=case["question"],
                context=context,
                answer=response.answer,
                expected_no_answer=(
                    expected_no_answer
                ),
            )

            judge_response = (
                llm_service.generate(
                    prompt=judge_prompt,
                    instructions=JUDGE_INSTRUCTIONS,
                )
            )

            judgment = parse_judge_response(
                judge_response
            )

            correct_count += int(
                judgment["correct"]
            )

            grounded_count += int(
                judgment["grounded"]
            )

            complete_count += int(
                judgment["complete"]
            )

            abstention_count += int(
                judgment[
                    "abstention_correct"
                ]
            )

            judge_passed = all(
                [
                    judgment["correct"],
                    judgment["grounded"],
                    judgment["complete"],
                    judgment[
                        "abstention_correct"
                    ],
                ]
            )

            judge_pass_count += int(
                judge_passed
            )

            end_to_end_passed = (
                judge_passed
                and source_requirement_passed
            )

            end_to_end_pass_count += int(
                end_to_end_passed
            )

            print()
            print(
                f"=== {case['id']} ==="
            )
            print(
                f"Question: "
                f"{case['question']}"
            )
            print(
                "Expected no-answer: "
                f"{expected_no_answer}"
            )
            print(
                "Selected source IDs: "
                f"{selected_document_ids}"
            )

            if expected_no_answer:
                print(
                    "Pipeline stage: "
                    + (
                        "REJECTED BEFORE LLM"
                        if not response.sources
                        else "LLM CALLED"
                    )
                )
            else:
                print(
                    "Expected source present: "
                    f"{source_requirement_passed}"
                )

            print(
                f"Answer: "
                f"{response.answer}"
            )

            print(
                f"Correct: "
                f"{judgment['correct']}"
            )
            print(
                f"Grounded: "
                f"{judgment['grounded']}"
            )
            print(
                f"Complete: "
                f"{judgment['complete']}"
            )
            print(
                "Abstention correct: "
                f"{judgment['abstention_correct']}"
            )
            print(
                f"Reason: "
                f"{judgment['reason']}"
            )

            print(
                "End-to-end result: "
                + (
                    "PASS"
                    if end_to_end_passed
                    else "FAIL"
                )
            )

        print()
        print(
            "=== End-to-End RAG Summary ==="
        )

        print(
            "Expected-source hit: "
            f"{expected_source_hits}/"
            f"{answerable_cases} "
            f"= "
            f"{expected_source_hits / answerable_cases:.2%}"
        )

        print(
            "Pre-LLM no-answer rejection: "
            f"{pre_llm_rejections}/"
            f"{no_answer_cases} "
            f"= "
            f"{pre_llm_rejections / no_answer_cases:.2%}"
        )

        print(
            "Correctness: "
            f"{correct_count}/{total_cases} "
            f"= "
            f"{correct_count / total_cases:.2%}"
        )

        print(
            "Groundedness: "
            f"{grounded_count}/{total_cases} "
            f"= "
            f"{grounded_count / total_cases:.2%}"
        )

        print(
            "Completeness: "
            f"{complete_count}/{total_cases} "
            f"= "
            f"{complete_count / total_cases:.2%}"
        )

        print(
            "Abstention compliance: "
            f"{abstention_count}/"
            f"{total_cases} "
            f"= "
            f"{abstention_count / total_cases:.2%}"
        )

        print(
            "Judge pass: "
            f"{judge_pass_count}/"
            f"{total_cases} "
            f"= "
            f"{judge_pass_count / total_cases:.2%}"
        )

        print(
            "End-to-end pass: "
            f"{end_to_end_pass_count}/"
            f"{total_cases} "
            f"= "
            f"{end_to_end_pass_count / total_cases:.2%}"
        )

    finally:
        print()
        print(
            "Rolling back evaluation data..."
        )

        db.rollback()
        db.close()

        print(
            "Evaluation data rolled back."
        )


if __name__ == "__main__":
    evaluate()