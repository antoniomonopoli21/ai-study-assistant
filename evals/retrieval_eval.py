import numpy as np

from app.config import settings
from app.services.embeddings import embedding_service
from evals.retrieval_dataset import DOCUMENTS, EVAL_CASES


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

        predicted_has_answer = (
            best_distance <= settings.rag_max_distance
        )

        expected_id = case["expected_id"]
        expected_has_answer = expected_id is not None

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


if __name__ == "__main__":
    evaluate()