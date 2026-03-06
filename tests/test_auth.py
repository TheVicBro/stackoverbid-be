"""
TC1 – Correct login returns JWT.
TC2 – Wrong credentials are rejected.
Additional: signup validation (duplicate username, short password, short username).
"""
from tests.conftest import auth_header


# ── TC1 · Correct Login ─────────────────────────────────────────────────────
class TestLogin:
    def test_login_success(self, client, create_user):
        """TC1 – Logging in with valid credentials returns an access token."""
        user, _ = create_user(username="alice", password="password123")
        resp = client.post("/auth/login", json={"username": "alice", "password": "password123"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client, create_user):
        """TC2 – Wrong password is rejected."""
        create_user(username="alice", password="password123")
        resp = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
        assert resp.status_code == 400

    def test_login_nonexistent_user(self, client):
        """TC2 variant – User does not exist."""
        resp = client.post("/auth/login", json={"username": "ghost", "password": "whatever1"})
        assert resp.status_code == 400

    def test_login_empty_username(self, client):
        """Empty username rejected by schema validation."""
        resp = client.post("/auth/login", json={"username": "", "password": "password123"})
        assert resp.status_code == 422

    def test_login_empty_password(self, client):
        """Empty password rejected by schema validation."""
        resp = client.post("/auth/login", json={"username": "alice", "password": ""})
        assert resp.status_code == 422


# ── Signup ───────────────────────────────────────────────────────────────────
class TestSignup:
    def test_signup_success(self, client):
        payload = {
            "username": "newuser",
            "password": "password123",
            "first_name": "New",
            "last_name": "User",
            "address": "456 New St",
        }
        resp = client.post("/auth/signup", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["username"] == "newuser"
        assert "id" in body

    def test_signup_duplicate_username(self, client, create_user):
        create_user(username="dup", password="password123")
        payload = {
            "username": "dup",
            "password": "password123",
            "first_name": "A",
            "last_name": "B",
            "address": "addr",
        }
        resp = client.post("/auth/signup", json=payload)
        assert resp.status_code == 400

    def test_signup_short_username(self, client):
        payload = {
            "username": "ab",
            "password": "password123",
            "first_name": "A",
            "last_name": "B",
            "address": "addr",
        }
        resp = client.post("/auth/signup", json=payload)
        assert resp.status_code == 422

    def test_signup_short_password(self, client):
        payload = {
            "username": "validuser",
            "password": "short",
            "first_name": "A",
            "last_name": "B",
            "address": "addr",
        }
        resp = client.post("/auth/signup", json=payload)
        assert resp.status_code == 422

    def test_signup_login_roundtrip(self, client):
        """Sign up, then log in with the same creds — full happy path."""
        payload = {
            "username": "roundtrip",
            "password": "password123",
            "first_name": "R",
            "last_name": "T",
            "address": "addr",
        }
        client.post("/auth/signup", json=payload)
        resp = client.post("/auth/login", json={"username": "roundtrip", "password": "password123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_protected_endpoint_without_token(self, client):
        """Accessing a protected endpoint without auth returns 401."""
        resp = client.get("/catalogue/items")
        assert resp.status_code == 401
