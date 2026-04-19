# app/lib/auth/store.py
# In-memory User store. Keyed by User.id (UUID string).
# Empty at import time; populated by app.lib.seed.seed.seed() at startup.
# Source of pattern: .planning/codebase/CONVENTIONS.md + 01-PATTERNS.md.
from datetime import datetime

from app.lib.auth.models import User

users_db: dict[str, User] = {}

# Password reset token store (D-04, D-06).
# Keyed by email. Value: {"token": UUID str, "expires_at": datetime}.
# In-memory only — resets on process restart (demo-appropriate).
reset_tokens_db: dict[str, dict[str, str | datetime]] = {}
