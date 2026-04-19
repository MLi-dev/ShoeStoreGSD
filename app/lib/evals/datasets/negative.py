# app/lib/evals/datasets/negative.py
# Negative eval cases — agent behavior under error/failure conditions.
# Format: {input, expected_trajectory, expected_output, tags}
# Source: REQUIREMENTS.md TEST-02, TEST-04; CONTEXT.md D-07, D-10
from deepeval.dataset import EvaluationDataset

CASES: list[dict] = [
    {
        "input": "Check out my cart with credit card",
        "expected_trajectory": ["view_cart", "checkout"],
        "expected_output": "out of stock",
        "tags": ["negative", "out-of-stock", "TEST-02"],
    },
    {
        "input": "Buy these shoes with Apple Pay",
        "expected_trajectory": ["view_cart", "checkout"],
        "expected_output": "payment",
        "tags": ["negative", "payment-failure", "TEST-02"],
    },
    {
        "input": "Cancel my order",
        "expected_trajectory": ["check_order_status"],
        "expected_output": "which order",
        "tags": ["negative", "cancel-no-id", "TEST-02"],
    },
    {
        "input": "I want to return my delivered order",
        "expected_trajectory": ["check_order_status"],
        "expected_output": "cannot",
        "tags": ["negative", "non-returnable", "TEST-02"],
    },
    {
        "input": "Show me order ORD-0001 details",
        "expected_trajectory": ["check_order_status"],
        "expected_output": "access",
        "tags": ["negative", "wrong-user", "TEST-02"],
    },
]

dataset = EvaluationDataset(goldens=[])  # populated by runner via CASES
