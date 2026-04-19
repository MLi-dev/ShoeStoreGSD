# tests/unit/test_config_jwt.py
# TDD tests for JWT constants in config.py (Task 1, Plan 02-01).


def test_jwt_secret_exists():
    from config import JWT_SECRET

    assert isinstance(JWT_SECRET, str)
    assert len(JWT_SECRET) > 0


def test_jwt_algorithm_is_hs256():
    from config import JWT_ALGORITHM

    assert JWT_ALGORITHM == "HS256"


def test_jwt_expire_minutes_is_30():
    from config import JWT_EXPIRE_MINUTES

    assert JWT_EXPIRE_MINUTES == 30
