# app/lib/auth/models.py
# User domain model. Plain @dataclass per CLAUDE.md directive
# (Pydantic is reserved for FastAPI request/response schemas, not domain objects).
# Source of shape: .planning/codebase/CONVENTIONS.md lines 50-58.
from dataclasses import dataclass


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    created_at: str
