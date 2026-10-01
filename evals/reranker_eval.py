from types import SimpleNamespace

import numpy as np

from app.config import settings
from app.services.embeddings import embedding_service
from app.services.reranker import reranker_service
from evals.retrieval_dataset import DOCUMENTS, EVAL_CASES


EVAL_REQUEST_LIMIT = 3

RERANKER_THRESHOLDS = [
    -3.0,
    -2.0,
    -1.0,
    0.0,
    0.5,
    0.6,
    1.0,
    2.0,
    3.0,
]


def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    return float(
        np.dot(vector_a, vector_b)
    )


def evaluate():
    print("Embedding documents...")

    document_embeddings_list = (
        embedding_service.embed_passages(
            [
                document["text"]
                for document in DOCUMENTS
            ]
        )
    )

    document_embeddings = {
        document["id"]: embedding
        for document, embedding in zip(
            DOCUMENTS,
            document_embeddings_list,
            strict=True,
        )
    }

    chunks_by_id = {
        document["id"]: SimpleNamespace(
            id=index,
            note_id=index,
            chunk_index=0,
            content=document["text"],
            eval_id=document["id"],
        )
        for index, document in enumerate(
            DOCUMENTS,
            start=1,
        )
    }

    candidate_limit = max(
        EVAL_REQUEST_LIMIT,
        settings.reranker_candidate_k,
    )

    print()
    print("=== Production Configuration ===")
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
        f"Evaluation request limit: "
        f"{EVAL_REQUEST_LIMIT}"
    )
    print(
        f"Effective candidate limit: "
        f"{candidate_limit}"
    )

    retrieval_hit_at_1 = 0
    reranker_hit_at_1 = 0
    selected_hit_at_1 = 0

    answerable_cases = 0
    answerable_accepted = 0

    no_answer_cases = 0
    correct_rejections = 0

    answerability_correct = 0
    pipeline_correct = 0

    positive_scores = []
    negative_scores = []

    positive_examples = []
    negative_examples = []

    answerability_examples = []

    for case in EVAL_CASES:
        question = case["question"]
        expected_id = case["expected_id"]

        query_embedding = (
            embedding_service.embed_query(
                question
            )
        )

        retrieval_results = []

        for document in DOCUMENTS:
            similarity = cosine_similarity(
                query_embedding,
                document_embeddings[
                    document["id"]
                ],
            )

            distance = 1.0 - similarity

            retrieval_results.append(
                (
                    document["id"],
                    distance,
                    similarity,
                )
            )

        retrieval_results.sort(
            key=lambda item: (
                item[1],
                item[0],
            )
        )

        retrieved_candidates = retrieval_results[
            :candidate_limit
        ]

        candidates = [
            (
                chunks_by_id[document_id],
                distance,
            )
            for (
                document_id,
                distance,
                similarity,
            ) in retrieved_candidates
        ]

        reranked_results = (
            reranker_service.rerank(
                query=question,
                candidates=candidates,
            )
        )

        relevant_results = [
            result
            for result in reranked_results
            if (
                result[2]
                >= settings.reranker_threshold
            )
        ]

        selected_results = relevant_results[
            :EVAL_REQUEST_LIMIT
        ]

        predicted_has_answer = bool(
            selected_results
        )

        expected_has_answer = (
            expected_id is not None
        )

        if (
            predicted_has_answer
            == expected_has_answer
        ):
            answerability_correct += 1

        retrieval_top_id = (
            retrieved_candidates[0][0]
        )

        reranker_top_id = (
            reranked_results[0][0].eval_id
        )

        selected_ids = [
            chunk.eval_id
            for (
                chunk,
                distance,
                score,
            ) in selected_results
        ]

        if expected_has_answer:
            answerable_cases += 1

            if retrieval_top_id == expected_id:
                retrieval_hit_at_1 += 1

            if reranker_top_id == expected_id:
                reranker_hit_at_1 += 1

            if predicted_has_answer:
                answerable_accepted += 1

            if (
                selected_ids
                and selected_ids[0]
                == expected_id
            ):
                selected_hit_at_1 += 1

            if expected_id in selected_ids:
                pipeline_correct += 1

            expected_score = None

            for (
                chunk,
                distance,
                reranker_score,
            ) in reranked_results:
                if chunk.eval_id == expected_id:
                    expected_score = reranker_score
                    break

            if expected_score is not None:
                positive_scores.append(
                    expected_score
                )

                positive_examples.append(
                    (
                        expected_score,
                        question,
                        expected_id,
                    )
                )

        else:
            no_answer_cases += 1

            if not predicted_has_answer:
                correct_rejections += 1
                pipeline_correct += 1

            top_score = (
                reranked_results[0][2]
            )

            negative_scores.append(
                top_score
            )

            negative_examples.append(
                (
                    top_score,
                    question,
                    reranker_top_id,
                )
            )

        top_reranker_score = (
            reranked_results[0][2]
        )

        answerability_examples.append(
            (
                top_reranker_score,
                expected_has_answer,
            )
        )

        print()
        print(
            f"Question: {question}"
        )
        print(
            f"Expected: {expected_id}"
        )
        print(
            f"Retrieval top 1: "
            f"{retrieval_top_id}"
        )
        print(
            f"Reranker top 1: "
            f"{reranker_top_id} "
            f"(score="
            f"{top_reranker_score:.4f})"
        )
        print(
            "Production decision: "
            + (
                "ANSWER"
                if predicted_has_answer
                else "NO ANSWER"
            )
        )

        print(
            f"Selected sources: "
            f"{selected_ids}"
        )

        print("Reranked candidates:")

        for (
            chunk,
            distance,
            reranker_score,
        ) in reranked_results:
            print(
                f"  {chunk.eval_id}: "
                f"distance={distance:.4f}, "
                f"reranker={reranker_score:.4f}"
            )

    total_cases = len(EVAL_CASES)

    print()
    print(
        "=== Production Pipeline Evaluation ==="
    )

    print(
        "Retrieval Hit@1: "
        f"{retrieval_hit_at_1}/"
        f"{answerable_cases} "
        f"= "
        f"{retrieval_hit_at_1 / answerable_cases:.2%}"
    )

    print(
        "Reranker Hit@1: "
        f"{reranker_hit_at_1}/"
        f"{answerable_cases} "
        f"= "
        f"{reranker_hit_at_1 / answerable_cases:.2%}"
    )

    print(
        "Selected Hit@1: "
        f"{selected_hit_at_1}/"
        f"{answerable_cases} "
        f"= "
        f"{selected_hit_at_1 / answerable_cases:.2%}"
    )

    print(
        "Answerable accepted: "
        f"{answerable_accepted}/"
        f"{answerable_cases} "
        f"= "
        f"{answerable_accepted / answerable_cases:.2%}"
    )

    print(
        "No-answer rejection: "
        f"{correct_rejections}/"
        f"{no_answer_cases} "
        f"= "
        f"{correct_rejections / no_answer_cases:.2%}"
    )

    print(
        "Answerability accuracy: "
        f"{answerability_correct}/"
        f"{total_cases} "
        f"= "
        f"{answerability_correct / total_cases:.2%}"
    )

    print(
        "Pipeline success: "
        f"{pipeline_correct}/"
        f"{total_cases} "
        f"= "
        f"{pipeline_correct / total_cases:.2%}"
    )

    if positive_scores:
        print(
            "Minimum positive score: "
            f"{min(positive_scores):.4f}"
        )

        print(
            "Average positive score: "
            f"{np.mean(positive_scores):.4f}"
        )

    if negative_scores:
        print(
            "Maximum no-answer score: "
            f"{max(negative_scores):.4f}"
        )

        print(
            "Average no-answer score: "
            f"{np.mean(negative_scores):.4f}"
        )

    print()
    print("=== Lowest Positive Scores ===")

    for (
        score,
        question,
        document_id,
    ) in sorted(
        positive_examples,
        key=lambda item: item[0],
    )[:5]:
        print(
            f"{score:.4f} | "
            f"{document_id} | "
            f"{question}"
        )

    print()
    print("=== Highest No-Answer Scores ===")

    for (
        score,
        question,
        document_id,
    ) in sorted(
        negative_examples,
        key=lambda item: item[0],
        reverse=True,
    )[:5]:
        print(
            f"{score:.4f} | "
            f"{document_id} | "
            f"{question}"
        )

    print()
    print(
        "=== Experimental Threshold Comparison ==="
    )

    for threshold in RERANKER_THRESHOLDS:
        correct = 0
        answerable_correct = 0
        no_answer_correct = 0

        for (
            score,
            expected_has_answer,
        ) in answerability_examples:
            predicted_has_answer = (
                score >= threshold
            )

            if (
                predicted_has_answer
                == expected_has_answer
            ):
                correct += 1

                if expected_has_answer:
                    answerable_correct += 1
                else:
                    no_answer_correct += 1

        overall_accuracy = (
            correct / total_cases
        )

        answerable_accuracy = (
            answerable_correct
            / answerable_cases
        )

        no_answer_accuracy = (
            no_answer_correct
            / no_answer_cases
        )

        marker = ""

        if (
            threshold
            == settings.reranker_threshold
        ):
            marker = " <-- production"

        print(
            f"threshold={threshold:>4.1f} | "
            f"overall={overall_accuracy:.2%} | "
            f"answerable={answerable_accuracy:.2%} | "
            f"no-answer={no_answer_accuracy:.2%}"
            f"{marker}"
        )


if __name__ == "__main__":
    evaluate()