from types import SimpleNamespace

from app.config import settings
from app.services.llm import llm_service
from app.services.rag import (
    RAG_INSTRUCTIONS,
    build_rag_prompt,
)
from evals.answer_dataset import (
    ANSWER_EVAL_CASES,
)
from evals.retrieval_dataset import DOCUMENTS

import re
import unicodedata

NO_ANSWER_MARKERS = [
    "do not have enough information",
    "don't have enough information",
    "not enough information",
    "insufficient information",

    "notes do not explain",
    "notes don't explain",
    "context does not explain",
    "context doesn't explain",

    "non ho abbastanza informazioni",
    "non ci sono abbastanza informazioni",
    "informazioni insufficienti",
    "gli appunti non spiegano",
    "il contesto non spiega",
]

def normalize_text(text: str) -> str:
    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    text = (
        text
        .replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
    )

    text = text.lower()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()

def contains_any(
    text: str,
    alternatives: list[str],
) -> bool:
    normalized_text = normalize_text(
        text
    )

    return any(
        normalize_text(alternative)
        in normalized_text
        for alternative in alternatives
    )


def is_no_answer(response: str) -> bool:
    return contains_any(
        response,
        NO_ANSWER_MARKERS,
    )


def evaluate():
    documents_by_id = {
        document["id"]: document
        for document in DOCUMENTS
    }

    total_cases = len(
        ANSWER_EVAL_CASES
    )

    answerable_cases = 0
    no_answer_cases = 0

    answerable_passed = 0
    no_answer_passed = 0
    overall_passed = 0

    print(
        "=== Answer Evaluation Configuration ==="
    )
    print(
        f"LLM model: {settings.openai_model}"
    )
    print(
        f"Cases: {total_cases}"
    )

    for case_index, case in enumerate(
        ANSWER_EVAL_CASES,
        start=1,
    ):
        chunks = []

        for chunk_index, document_id in enumerate(
            case["context_ids"]
        ):
            document = documents_by_id[
                document_id
            ]

            chunks.append(
                SimpleNamespace(
                    note_id=case_index,
                    chunk_index=chunk_index,
                    content=document["text"],
                )
            )

        prompt = build_rag_prompt(
            question=case["question"],
            chunks=chunks,
        )

        answer = llm_service.generate(
            prompt=prompt,
            instructions=RAG_INSTRUCTIONS,
        )

        expected_no_answer = (
            case["expected_no_answer"]
        )

        print()
        print(
            f"=== {case['id']} ==="
        )
        print(
            f"Question: {case['question']}"
        )
        print(
            "Context IDs: "
            f"{case['context_ids']}"
        )
        print(
            f"Answer: {answer}"
        )

        if expected_no_answer:
            no_answer_cases += 1

            passed = is_no_answer(
                answer
            )

            if passed:
                no_answer_passed += 1

            print(
                "Expected behavior: NO ANSWER"
            )

        else:
            answerable_cases += 1

            concept_results = []

            for concept_group in case[
                "required_concepts"
            ]:
                concept_found = contains_any(
                    answer,
                    concept_group,
                )

                concept_results.append(
                    (
                        concept_group,
                        concept_found,
                    )
                )

            concepts_passed = all(
                found
                for group, found
                in concept_results
            )

            refused = is_no_answer(
                answer
            )

            passed = (
                concepts_passed
                and not refused
            )

            if passed:
                answerable_passed += 1

            print(
                "Required concepts:"
            )

            for (
                concept_group,
                found,
            ) in concept_results:
                print(
                    f"  {concept_group}: "
                    + (
                        "PASS"
                        if found
                        else "FAIL"
                    )
                )

            print(
                f"Unexpected refusal: "
                f"{refused}"
            )

        if passed:
            overall_passed += 1

        print(
            "Case result: "
            + (
                "PASS"
                if passed
                else "FAIL"
            )
        )

    print()
    print(
        "=== Answer Evaluation Summary ==="
    )

    print(
        "Answerable correctness: "
        f"{answerable_passed}/"
        f"{answerable_cases} "
        f"= "
        f"{answerable_passed / answerable_cases:.2%}"
    )

    print(
        "No-answer compliance: "
        f"{no_answer_passed}/"
        f"{no_answer_cases} "
        f"= "
        f"{no_answer_passed / no_answer_cases:.2%}"
    )

    print(
        "Overall deterministic score: "
        f"{overall_passed}/"
        f"{total_cases} "
        f"= "
        f"{overall_passed / total_cases:.2%}"
    )


if __name__ == "__main__":
    evaluate()