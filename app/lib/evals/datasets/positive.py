# app/lib/evals/datasets/positive.py
# Positive eval cases — successful happy-path agent interactions.
# Format: {input, expected_trajectory, expected_output, tags}
# Source: REQUIREMENTS.md TEST-01, TEST-04; CONTEXT.md D-07, D-09
from deepeval.dataset import EvaluationDataset

CASES: list[dict] = [
    {
        "input": "Show me running shoes under $150",
        "expected_trajectory": ["search_products"],
        "expected_output": "running",
        "tags": ["positive", "search", "TEST-01"],
    },
    {
        "input": "Add the first running shoe in size 10 to my cart",
        "expected_trajectory": ["search_products", "add_to_cart"],
        "expected_output": "cart",
        "tags": ["positive", "add-to-cart", "TEST-01"],
    },
    {
        "input": "Check out my cart using PayPal",
        "expected_trajectory": ["view_cart", "checkout"],
        "expected_output": "order",
        "tags": ["positive", "checkout", "TEST-01"],
    },
    {
        "input": "What is the status of my most recent order?",
        "expected_trajectory": ["check_order_status"],
        "expected_output": "order",
        "tags": ["positive", "order-status", "TEST-01"],
    },
    {
        "input": "Please cancel my most recent order",
        "expected_trajectory": ["check_order_status", "cancel_order"],
        "expected_output": "cancel",
        "tags": ["positive", "cancel", "TEST-01"],
    },
]

dataset = EvaluationDataset(goldens=[])  # populated by runner via CASES
