ANSWER_EVAL_CASES = [
    {
        "id": "improper_integrals",
        "question": (
            "When does an improper integral converge?"
        ),
        "context_ids": [
            "improper_integrals",
        ],
        "required_concepts": [
            ["limit"],
            ["exists"],
            ["finite"],
        ],
        "expected_no_answer": False,
    },
    {
        "id": "geometric_series_it",
        "question": (
            "Quando converge una serie geometrica?"
        ),
        "context_ids": [
            "geometric_series",
        ],
        "required_concepts": [
            ["q"],
            [ "less than one",
            "less than 1",
            "minore di uno",
            "minore di 1",
            "<1",
            "< 1",
            ],
        ],
        "expected_no_answer": False,
    },
    {
        "id": "newton_it",
        "question": (
            "Qual è la relazione tra forza, massa "
            "e accelerazione?"
        ),
        "context_ids": [
            "newton_second_law",
        ],
        "required_concepts": [
            ["forza", "force"],
            ["massa", "mass"],
            ["accelerazione", "acceleration"],
        ],
        "expected_no_answer": False,
    },
    {
        "id": "sql_group_by",
        "question": (
            "What is GROUP BY used for?"
        ),
        "context_ids": [
            "sql_group_by",
        ],
        "required_concepts": [
            ["group"],
            ["aggregate"],
        ],
        "expected_no_answer": False,
    },
    {
        "id": "recursion_it",
        "question": (
            "Perché una funzione ricorsiva "
            "ha bisogno di un caso base?"
        ),
        "context_ids": [
            "recursion",
        ],
        "required_concepts": [
            ["caso base", "base case"],
            ["termin", "fin"],
        ],
        "expected_no_answer": False,
    },
    {
        "id": "eigenvalues",
        "question": (
            "What is the relationship between "
            "an eigenvector and its eigenvalue?"
        ),
        "context_ids": [
            "eigenvalues",
        ],
        "required_concepts": [
            ["eigenvector"],
            ["direction"],
            ["eigenvalue"],
            ["scal", "factor"],
        ],
        "expected_no_answer": False,
    },

    # The context is related, but it does NOT contain
    # enough information to answer the question.
    {
        "id": "sql_having_no_answer",
        "question": (
            "What is the SQL HAVING clause used for?"
        ),
        "context_ids": [
            "sql_join",
            "sql_group_by",
        ],
        "required_concepts": [],
        "expected_no_answer": True,
    },
    {
        "id": "associative_cache_no_answer",
        "question": (
            "How does a fully associative cache work?"
        ),
        "context_ids": [
            "cache_direct_mapping",
        ],
        "required_concepts": [],
        "expected_no_answer": True,
    },
    {
        "id": "bayes_no_answer",
        "question": (
            "What does Bayes' theorem state?"
        ),
        "context_ids": [
            "conditional_probability",
        ],
        "required_concepts": [],
        "expected_no_answer": True,
    },
    {
        "id": "second_derivative_no_answer",
        "question": (
            "What is the second derivative used for?"
        ),
        "context_ids": [
            "derivatives",
        ],
        "required_concepts": [],
        "expected_no_answer": True,
    },
]