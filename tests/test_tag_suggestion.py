from tests.conftest import auth_header


class TestSuggestTags:
    def test_suggest_tags_requires_auth(self, client):
        resp = client.post("/auction/items/suggest-tags", json={"title": "laptop", "description": ""})
        assert resp.status_code == 401

    def test_suggest_tags_heuristic_laptop_is_electronics(self, client, create_user, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        _, token = create_user()
        resp = client.post(
            "/auction/items/suggest-tags",
            headers=auth_header(token),
            json={"title": "Gaming laptop RTX", "description": "Great for school"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["source"] == "heuristic"
        assert "Electronics" in body["tags"]


class TestItemTags:
    def test_create_item_with_tags(self, client, create_user):
        _, token = create_user(username="seller_tags", password="password123")
        resp = client.post(
            "/auction/items",
            headers=auth_header(token),
            json={
                "title": "Tagged item",
                "description": "Desc",
                "starting_price": 10.0,
                "end_time": "2099-01-15T12:00:00Z",
                "tags": ["Electronics", "Collectibles"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert set(data["tags"]) == {"Electronics", "Collectibles"}

    def test_search_matches_tag_not_in_title(self, client, create_user):
        _, seller_token = create_user(username="seller_tagsearch", password="password123")
        _, buyer_token = create_user(username="buyer_tagsearch", password="password123")
        create = client.post(
            "/auction/items",
            headers=auth_header(seller_token),
            json={
                "title": "Plain box",
                "description": "No fashion words here.",
                "starting_price": 5.0,
                "end_time": "2099-02-01T12:00:00Z",
                "tags": ["Fashion"],
            },
        )
        assert create.status_code == 200

        resp = client.get("/catalogue/items", params={"keyword": "Fashion"}, headers=auth_header(buyer_token))
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 1
        assert any(i["title"] == "Plain box" for i in items)
