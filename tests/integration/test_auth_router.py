# tests/integration/test_auth_router.py
import pytest

# All tests in this file require auth_router to be registered in main.py.
# They are marked xfail until Wave 2 (plan 03) completes.

@pytest.mark.xfail(strict=False, reason="auth_router not yet implemented")
def test_login_sets_httponly_cookie(client):
    resp = client.post("/auth/login", data={"email": "alice@example.com", "password": "alice-demo-password-2026"})
    assert resp.status_code == 303
    assert "access_token" in resp.cookies
    # httpOnly cookies are not readable in Set-Cookie header by JS — validate attribute
    set_cookie_header = resp.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie_header

@pytest.mark.xfail(strict=False, reason="auth_router not yet implemented")
def test_login_invalid_credentials_returns_form_with_error(client):
    resp = client.post("/auth/login", data={"email": "alice@example.com", "password": "wrong"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.content

@pytest.mark.xfail(strict=False, reason="auth_router not yet implemented")
def test_logout_deletes_cookie(auth_client):
    resp = auth_client.post("/auth/logout")
    assert resp.status_code == 303
    # Cookie should be cleared (max-age=0 or deleted)
    set_cookie_header = resp.headers.get("set-cookie", "")
    assert "access_token" in set_cookie_header

@pytest.mark.xfail(strict=False, reason="auth_router not yet implemented")
def test_register_new_user_redirects(client):
    resp = client.post("/auth/register", data={"email": "new@example.com", "password": "secret123"})
    assert resp.status_code == 303

@pytest.mark.xfail(strict=False, reason="auth_router not yet implemented")
def test_protected_route_redirects_to_login_when_unauthenticated(client):
    resp = client.get("/cart")
    assert resp.status_code == 307
    assert "/login" in resp.headers.get("location", "")

@pytest.mark.xfail(strict=False, reason="auth_router not yet implemented")
def test_next_param_open_redirect_is_blocked(client):
    """Absolute URL in ?next= must not be honored — must redirect to /products."""
    resp = client.post(
        "/auth/login",
        data={"email": "alice@example.com", "password": "alice-demo-password-2026"},
        params={"next": "https://evil.com"},
    )
    assert resp.status_code == 303
    location = resp.headers.get("location", "")
    assert not location.startswith("https://evil.com")
    assert not location.startswith("//")
