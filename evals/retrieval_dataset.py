DOCUMENTS = [
    {
        "id": "improper_integrals",
        "text": (
            "An improper integral converges when the limit "
            "that defines the integral exists and is finite."
        ),
    },
    {
        "id": "geometric_series",
        "text": (
            "A geometric series with ratio q converges when "
            "the absolute value of q is less than one."
        ),
    },
    {
        "id": "derivatives",
        "text": (
            "The derivative of a function measures its instantaneous "
            "rate of change with respect to its variable."
        ),
    },
    {
        "id": "newton_second_law",
        "text": (
            "Newton's second law states that the net force acting "
            "on an object equals mass multiplied by acceleration."
        ),
    },
    {
        "id": "kinetic_energy",
        "text": (
            "The kinetic energy of an object is one half of its mass "
            "multiplied by the square of its velocity."
        ),
    },
    {
        "id": "sql_join",
        "text": (
            "A SQL JOIN combines rows from two or more tables "
            "according to a related column."
        ),
    },
    {
        "id": "sql_group_by",
        "text": (
            "The SQL GROUP BY clause groups rows that share the same "
            "values so aggregate functions can be applied to each group."
        ),
    },
    {
        "id": "recursion",
        "text": (
            "A recursive function calls itself on smaller instances "
            "of the same problem and requires a base case to terminate."
        ),
    },
    {
        "id": "divide_and_conquer",
        "text": (
            "Divide and conquer splits a problem into smaller "
            "subproblems, solves them independently, and combines "
            "their solutions."
        ),
    },
    {
        "id": "conditional_probability",
        "text": (
            "Conditional probability measures the probability of "
            "an event A given that another event B has occurred."
        ),
    },
    {
        "id": "eigenvalues",
        "text": (
            "An eigenvector of a matrix is a nonzero vector whose "
            "direction is unchanged by the linear transformation. "
            "The corresponding scaling factor is the eigenvalue."
        ),
    },
    {
        "id": "cache_direct_mapping",
        "text": (
            "In a direct-mapped cache, each memory block can be stored "
            "in exactly one cache line determined by its index."
        ),
    },
]


EVAL_CASES = [
    {
        "question": (
            "When does an integral with an infinite endpoint converge?"
        ),
        "expected_id": "improper_integrals",
    },
    {
        "question": (
            "Quando converge una serie geometrica?"
        ),
        "expected_id": "geometric_series",
    },
    {
        "question": (
            "What does the derivative tell us about a function?"
        ),
        "expected_id": "derivatives",
    },
    {
        "question": (
            "Qual è la relazione tra forza, massa e accelerazione?"
        ),
        "expected_id": "newton_second_law",
    },
    {
        "question": (
            "How does velocity affect kinetic energy?"
        ),
        "expected_id": "kinetic_energy",
    },
    {
        "question": (
            "Come posso combinare righe provenienti da due tabelle SQL?"
        ),
        "expected_id": "sql_join",
    },
    {
        "question": (
            "Which SQL clause should I use before applying aggregate "
            "functions to groups of rows?"
        ),
        "expected_id": "sql_group_by",
    },
    {
        "question": (
            "Perché una funzione ricorsiva ha bisogno di un caso base?"
        ),
        "expected_id": "recursion",
    },
    {
        "question": (
            "Which algorithmic paradigm divides a problem into "
            "independent smaller problems and then combines the results?"
        ),
        "expected_id": "divide_and_conquer",
    },
    {
        "question": (
            "Come si interpreta la probabilità di A sapendo che B "
            "si è già verificato?"
        ),
        "expected_id": "conditional_probability",
    },
    {
        "question": (
            "What is the relationship between an eigenvector "
            "and its eigenvalue?"
        ),
        "expected_id": "eigenvalues",
    },
    {
        "question": (
            "In una cache direct mapped, dove può essere inserito "
            "un determinato blocco di memoria?"
        ),
        "expected_id": "cache_direct_mapping",
    },

    # Questions that should NOT be answerable from the dataset.
    {
        "question": "How does photosynthesis work?",
        "expected_id": None,
    },
    {
        "question": "Quali furono le cause della Rivoluzione francese?",
        "expected_id": None,
    },
    {
        "question": "How do neural networks perform backpropagation?",
        "expected_id": None,
    },
]