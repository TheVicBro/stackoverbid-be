from tests.conftest import auth_header



class TestLogin:
    def test_login_success(self, client, create_user):
        """Logging in with valid credentials returns an access token."""
        user, _ = create_user(username="alice", password="password123")
        resp = client.post("/auth/login", json={"username": "alice", "password": "password123"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client, create_user):
        """Wrong password is rejected."""
        create_user(username="alice", password="password123")
        resp = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
        assert resp.status_code == 400

    def test_login_nonexistent_user(self, client):
        """Non-existent user is rejected."""
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
        """Sign up, then log in with the same creds."""
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


class TestProfile:
    def test_patch_me_updates_address(self, client, create_user):
        user, token = create_user(username="pat", password="password123", address="Old Addr")
        resp = client.patch(
            "/auth/me",
            json={"address": "99 New Ship St, Boston MA"},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["address"] == "99 New Ship St, Boston MA"
        assert body["username"] == "pat"

        me = client.get("/auth/me", headers=auth_header(token))
        assert me.status_code == 200
        assert me.json()["address"] == "99 New Ship St, Boston MA"

    def test_put_me_updates_name(self, client, create_user):
        _, token = create_user(first_name="A", last_name="B")
        resp = client.put(
            "/auth/me",
            json={"first_name": "Putname"},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Putname"

    def test_post_profile_updates_name(self, client, create_user):
        _, token = create_user(first_name="X", last_name="Y")
        resp = client.post(
            "/auth/profile",
            json={"first_name": "Postname"},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Postname"

    def test_patch_me_empty_body(self, client, create_user):
        _, token = create_user()
        resp = client.patch("/auth/me", json={}, headers=auth_header(token))
        assert resp.status_code == 400

    def test_patch_me_name_only_preserves_address(self, client, create_user):
        _, token = create_user(first_name="Old", address="100 Keep St")
        resp = client.patch(
            "/auth/me",
            json={"first_name": "Newfirst"},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Newfirst"
        assert resp.json()["address"] == "100 Keep St"

    def test_patch_me_can_clear_address(self, client, create_user):
        _, token = create_user(address="Will Remove")
        resp = client.patch("/auth/me", json={"address": ""}, headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["address"] == ""
