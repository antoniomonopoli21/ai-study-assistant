import numpy as np

from app.config import settings
from app.services.embeddings import embedding_service
from evals.retrieval_dataset import DOCUMENTS, EVAL_CASES

THRESHOLDS = [
    0.15,
    0.18,
    0.20,
    0.22,
    0.25,
    0.28,
    0.30,
]

def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    return float(
        np.dot(vector_a, vector_b)
    )


def embed_documents():
    texts = [
        document["text"]
        for document in DOCUMENTS
    ]

    embeddings = embedding_service.embed_passages(texts)

    return {
        document["id"]: embedding
        for document, embedding in zip(
            DOCUMENTS,
            embeddings,
            strict=True,
        )
    }


def evaluate():
    document_embeddings = embed_documents()

    threshold_results = {
        threshold: {
            "correct": 0,
            "answerable_correct": 0,
            "no_answer_correct": 0,
        }
        for threshold in THRESHOLDS
}

    answerable_cases = 0
    hit_at_1 = 0
    hit_at_3 = 0

    no_answer_cases = 0
    correct_rejections = 0

    threshold_correct = 0

    for case in EVAL_CASES:
        query_embedding = embedding_service.embed_query(
            case["question"]
        )

        scored_documents = []

        for document in DOCUMENTS:
            similarity = cosine_similarity(
                query_embedding,
                document_embeddings[document["id"]],
            )

            scored_documents.append(
                (document["id"], similarity)
            )

        scored_documents.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        ranking = [
            document_id
            for document_id, similarity in scored_documents
        ]

        best_id, best_similarity = scored_documents[0]

        best_distance = 1.0 - best_similarity

        second_best_similarity = scored_documents[1][1]

        margin = (
            best_similarity
            - second_best_similarity
        )

        predicted_has_answer = (
            best_distance <= settings.rag_max_distance
        )

        expected_id = case["expected_id"]
        expected_has_answer = expected_id is not None

        for threshold in THRESHOLDS:
            threshold_predicts_answer = (
            best_distance <= threshold
            )

            if threshold_predicts_answer == expected_has_answer:
                threshold_results[threshold]["correct"] += 1

                if expected_has_answer:
                    threshold_results[threshold][
                        "answerable_correct"
                    ] += 1
                else:
                    threshold_results[threshold][
                        "no_answer_correct"
                    ] += 1

        if predicted_has_answer == expected_has_answer:
            threshold_correct += 1

        if expected_has_answer:
            answerable_cases += 1

            if expected_id in ranking[:1]:
                hit_at_1 += 1

            if expected_id in ranking[:3]:
                hit_at_3 += 1

        else:
            no_answer_cases += 1

            if not predicted_has_answer:
                correct_rejections += 1

        print()
        print(f"Question: {case['question']}")
        print(f"Expected: {expected_id}")
        print(f"Best result: {best_id}")
        print(f"Best similarity: {best_similarity:.4f}")
        print(f"Best distance: {best_distance:.4f}")
        print(f"Top1-Top2 margin: {margin:.4f}")
        print(
            "Threshold decision: "
            + (
                "ANSWER"
                if predicted_has_answer
                else "NO ANSWER"
            )
        )

        print("Top 3:")

        for document_id, similarity in scored_documents[:3]:
            print(
                f"  {document_id}: {similarity:.4f}"
            )

    total_cases = len(EVAL_CASES)

    print()
    print("=== Retrieval Evaluation ===")

    print(
        f"Hit@1: {hit_at_1}/{answerable_cases} "
        f"= {hit_at_1 / answerable_cases:.2%}"
    )

    print(
        f"Hit@3: {hit_at_3}/{answerable_cases} "
        f"= {hit_at_3 / answerable_cases:.2%}"
    )

    print(
        f"No-answer rejection: "
        f"{correct_rejections}/{no_answer_cases} "
        f"= {correct_rejections / no_answer_cases:.2%}"
    )

    print(
        f"Threshold accuracy: "
        f"{threshold_correct}/{total_cases} "
        f"= {threshold_correct / total_cases:.2%}"
    )

    print(
        f"RAG max distance: "
        f"{settings.rag_max_distance}"
    )

    print()
    print("=== Threshold Comparison ===")

    for threshold in THRESHOLDS:
        result = threshold_results[threshold]

        accuracy = (
            result["correct"]
            / total_cases
        )

        answerable_accuracy = (
            result["answerable_correct"]
            / answerable_cases
        )

        no_answer_accuracy = (
            result["no_answer_correct"]
            / no_answer_cases
        )

        print(
            f"threshold={threshold:.2f} | "
            f"overall={accuracy:.2%} | "
            f"answerable={answerable_accuracy:.2%} | "
            f"no-answer={no_answer_accuracy:.2%}"
        )

if __name__ == "__main__":
    evaluate()