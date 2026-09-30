import numpy as np
from sentence_transformers import CrossEncoder

from app.services.embeddings import embedding_service
from evals.retrieval_dataset import DOCUMENTS, EVAL_CASES


RERANKER_MODEL = (
    "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
)

TOP_K = 5

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

    documents_by_id = {
        document["id"]: document
        for document in DOCUMENTS
    }

    print("Loading reranker...")

    reranker = CrossEncoder(
        RERANKER_MODEL
    )

    retrieval_hit_at_1 = 0
    reranker_hit_at_1 = 0
    answerable_cases = 0

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

            retrieval_results.append(
                (
                    document["id"],
                    similarity,
                )
            )

        retrieval_results.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        candidates = retrieval_results[
            :TOP_K
        ]

        pairs = [
            (
                question,
                documents_by_id[
                    document_id
                ]["text"],
            )
            for document_id, similarity
            in candidates
        ]

        scores = reranker.predict(
            pairs
        )

        reranked_results = [
            (
                document_id,
                similarity,
                float(reranker_score),
            )
            for (
                document_id,
                similarity,
            ), reranker_score
            in zip(
                candidates,
                scores,
                strict=True,
            )
        ]

        reranked_results.sort(
            key=lambda item: item[2],
            reverse=True,
        )

        top_reranker_score = reranked_results[0][2]

        answerability_examples.append(
            (
                top_reranker_score,
                expected_id is not None,
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
            "Retrieval top 1: "
            f"{candidates[0][0]} "
            f"(similarity="
            f"{candidates[0][1]:.4f})"
        )

        print(
            "Reranker top 1: "
            f"{reranked_results[0][0]} "
            f"(score="
            f"{reranked_results[0][2]:.4f})"
        )

        print("Reranked top 5:")

        for (
            document_id,
            similarity,
            reranker_score,
        ) in reranked_results:
            print(
                f"  {document_id}: "
                f"retrieval={similarity:.4f}, "
                f"reranker={reranker_score:.4f}"
            )

        if expected_id is not None:
            answerable_cases += 1

            if (
                candidates[0][0]
                == expected_id
            ):
                retrieval_hit_at_1 += 1

            if (
                reranked_results[0][0]
                == expected_id
            ):
                reranker_hit_at_1 += 1

            for (
                document_id,
                similarity,
                reranker_score,
            ) in reranked_results:
                if document_id == expected_id:
                    positive_scores.append(
                        reranker_score
                    )

                    positive_examples.append(
                        (
                            reranker_score,
                            question,
                            document_id,
                        )
                    )

                    break

        else:
            best_negative_id = (
                reranked_results[0][0]
            )

            best_negative_score = (
                reranked_results[0][2]
            )

            negative_scores.append(
                best_negative_score
            )

            negative_examples.append(
                (
                    best_negative_score,
                    question,
                    best_negative_id,
                )
            )

    print()
    print(
        "=== Reranker Evaluation ==="
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

    if (
        positive_scores
        and negative_scores
    ):
        score_gap = (
            min(positive_scores)
            - max(negative_scores)
        )

        print(
            "Positive/negative score gap: "
            f"{score_gap:.4f}"
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
    print("=== Reranker Threshold Comparison ===")

    total_cases = len(answerability_examples)

    answerable_cases = sum(
        1
        for _, expected_has_answer
        in answerability_examples
        if expected_has_answer
    )

    no_answer_cases = (
        total_cases - answerable_cases
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

        print(
            f"threshold={threshold:>4.1f} | "
            f"overall={overall_accuracy:.2%} | "
            f"answerable={answerable_accuracy:.2%} | "
            f"no-answer={no_answer_accuracy:.2%}"
        )


if __name__ == "__main__":
    evaluate()