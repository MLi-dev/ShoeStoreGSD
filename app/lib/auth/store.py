# app/lib/auth/store.py
# In-memory User store. Keyed by User.id (UUID string).
# Empty at import time; populated by app.lib.seed.seed.seed() at startup.
# Source of pattern: .planning/codebase/CONVENTIONS.md + 01-PATTERNS.md.
from app.lib.auth.models import User

users_db: dict[str, User] = {}
