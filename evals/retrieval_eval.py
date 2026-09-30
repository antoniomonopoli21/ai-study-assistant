from app.services.embeddings import embedding_service


DOCUMENTS = [
    {
        "id": "integrals",
        "text": (
            "An improper integral converges when the limit "
            "that defines the integral exists and is finite."
        ),
    },
    {
        "id": "newton",
        "text": (
            "Newton's second law states that force equals "
            "mass multiplied by acceleration."
        ),
    },
    {
        "id": "sql",
        "text": (
            "A SQL join combines rows from two or more tables "
            "according to a related column."
        ),
    },
]


EVAL_CASES = [
    {
        "question": (
            "When does an integral with an infinite endpoint converge?"
        ),
        "expected_id": "integrals",
    },
    {
        "question": (
            "What relationship connects force, mass and acceleration?"
        ),
        "expected_id": "newton",
    },
    {
        "question": (
            "How can I combine rows from different database tables?"
        ),
        "expected_id": "sql",
    },
]

import numpy as np

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

    hit_at_1 = 0
    hit_at_3 = 0

    for case in EVAL_CASES:
        query_embedding = embedding_service.embed_query(
            case["question"]
        )

        scored_documents = []

        for document in DOCUMENTS:
            score = cosine_similarity(
                query_embedding,
                document_embeddings[document["id"]],
            )

            scored_documents.append(
                (document["id"], score)
            )

        scored_documents.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        ranking = [
            document_id
            for document_id, score in scored_documents
        ]

        expected_id = case["expected_id"]

        if expected_id in ranking[:1]:
            hit_at_1 += 1

        if expected_id in ranking[:3]:
            hit_at_3 += 1

        print()
        print(f"Question: {case['question']}")
        print(f"Expected: {expected_id}")
        print("Ranking:")

        for document_id, score in scored_documents:
            print(
                f"  {document_id}: {score:.4f}"
            )

    total = len(EVAL_CASES)

    print()
    print("=== Retrieval Evaluation ===")
    print(
        f"Hit@1: {hit_at_1}/{total} "
        f"= {hit_at_1 / total:.2%}"
    )
    print(
        f"Hit@3: {hit_at_3}/{total} "
        f"= {hit_at_3 / total:.2%}"
    )

if __name__ == "__main__":
    evaluate()