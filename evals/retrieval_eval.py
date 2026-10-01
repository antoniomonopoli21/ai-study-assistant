import numpy as np

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

    embeddings = embedding_service.embed_passages(
        texts
    )

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
    no_answer_best_similarities = []
    no_answer_best_distances = []
    no_answer_margins = []

    for case in EVAL_CASES:
        query_embedding = (
            embedding_service.embed_query(
                case["question"]
            )
        )

        scored_documents = []

        for document in DOCUMENTS:
            similarity = cosine_similarity(
                query_embedding,
                document_embeddings[
                    document["id"]
                ],
            )

            scored_documents.append(
                (
                    document["id"],
                    similarity,
                )
            )

        scored_documents.sort(
            key=lambda item: (
                -item[1],
                item[0],
            )
        )

        ranking = [
            document_id
            for document_id, similarity
            in scored_documents
        ]

        best_id, best_similarity = (
            scored_documents[0]
        )

        second_best_similarity = (
            scored_documents[1][1]
        )

        best_distance = (
            1.0 - best_similarity
        )

        margin = (
            best_similarity
            - second_best_similarity
        )

        expected_id = case["expected_id"]

        if expected_id is not None:
            answerable_cases += 1

            if expected_id in ranking[:1]:
                hit_at_1 += 1

            if expected_id in ranking[:3]:
                hit_at_3 += 1

        else:
            no_answer_cases += 1

            no_answer_best_similarities.append(
                best_similarity
            )

            no_answer_best_distances.append(
                best_distance
            )

            no_answer_margins.append(
                margin
            )

        print()
        print(
            f"Question: "
            f"{case['question']}"
        )
        print(
            f"Expected: "
            f"{expected_id}"
        )
        print(
            f"Best result: "
            f"{best_id}"
        )
        print(
            f"Best similarity: "
            f"{best_similarity:.4f}"
        )
        print(
            f"Best distance: "
            f"{best_distance:.4f}"
        )
        print(
            f"Top1-Top2 margin: "
            f"{margin:.4f}"
        )

        print("Top 3:")

        for (
            document_id,
            similarity,
        ) in scored_documents[:3]:
            print(
                f"  {document_id}: "
                f"{similarity:.4f}"
            )

    print()
    print(
        "=== Retrieval Ranking Evaluation ==="
    )

    print(
        f"Hit@1: "
        f"{hit_at_1}/{answerable_cases} "
        f"= "
        f"{hit_at_1 / answerable_cases:.2%}"
    )

    print(
        f"Hit@3: "
        f"{hit_at_3}/{answerable_cases} "
        f"= "
        f"{hit_at_3 / answerable_cases:.2%}"
    )

    print()
    print(
        "=== No-Answer Retrieval Diagnostics ==="
    )

    print(
        f"No-answer cases: "
        f"{no_answer_cases}"
    )

 
    if no_answer_cases:
        average_best_similarity = np.mean(
            no_answer_best_similarities
        )

        average_best_distance = np.mean(
            no_answer_best_distances
        )

        average_margin = np.mean(
            no_answer_margins
        )

        highest_no_answer_similarity = max(
            no_answer_best_similarities
        )

        print(
            "Average best similarity: "
            f"{average_best_similarity:.4f}"
        )

        print(
            "Average best distance: "
            f"{average_best_distance:.4f}"
        )

        print(
            "Average Top1-Top2 margin: "
            f"{average_margin:.4f}"
        )

        print(
            "Highest no-answer similarity: "
            f"{highest_no_answer_similarity:.4f}"
        )

if __name__ == "__main__":
    evaluate()