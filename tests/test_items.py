from datetime import datetime, timedelta, timezone

from tests.conftest import auth_header


def _future_iso() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()


class TestCreateItem:

    def test_create_item_success(self, client, create_user):
        """Valid item creation."""
        _, token = create_user(username="seller", password="password123")
        payload = {
            "title": "Brand New Widget",
            "description": "A widget in mint condition.",
            "starting_price": 25.0,
            "end_time": _future_iso(),
        }
        resp = client.post("/auction/items", json=payload, headers=auth_header(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Brand New Widget"
        assert body["starting_price"] == 25.0
        assert body["status"] == "active"

    def test_create_item_missing_title(self, client, create_user):
        """Empty title rejected."""
        _, token = create_user(username="seller", password="password123")
        payload = {
            "title": "",
            "description": "desc",
            "starting_price": 10.0,
            "end_time": _future_iso(),
        }
        resp = client.post("/auction/items", json=payload, headers=auth_header(token))
        assert resp.status_code == 422

    def test_create_item_negative_price(self, client, create_user):
        """Negative starting price rejected."""
        _, token = create_user(username="seller", password="password123")
        payload = {
            "title": "Widget",
            "description": "desc",
            "starting_price": -5.0,
            "end_time": _future_iso(),
        }
        resp = client.post("/auction/items", json=payload, headers=auth_header(token))
        assert resp.status_code == 422

    def test_create_item_past_end_time(self, client, create_user):
        """End time in the past rejected."""
        _, token = create_user(username="seller", password="password123")
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        payload = {
            "title": "Widget",
            "description": "desc",
            "starting_price": 10.0,
            "end_time": past,
        }
        resp = client.post("/auction/items", json=payload, headers=auth_header(token))
        assert resp.status_code == 422

    def test_create_item_missing_description(self, client, create_user):
        """Empty description rejected."""
        _, token = create_user(username="seller", password="password123")
        payload = {
            "title": "Widget",
            "description": "",
            "starting_price": 10.0,
            "end_time": _future_iso(),
        }
        resp = client.post("/auction/items", json=payload, headers=auth_header(token))
        assert resp.status_code == 422


class TestEditItem:

    def test_edit_title_no_bids(self, client, create_user, create_item):
        """Seller can edit title when there are no bids."""
        seller, token = create_user(username="seller", password="password123")
        item = create_item(seller_id=seller.id, title="Old Title")

        resp = client.patch(
            f"/auction/items/{item.id}",
            json={"title": "New Title"},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"

    def test_edit_description_no_bids(self, client, create_user, create_item):
        """Seller can edit description when there are no bids."""
        seller, token = create_user(username="seller", password="password123")
        item = create_item(seller_id=seller.id, description="Old desc")

        resp = client.patch(
            f"/auction/items/{item.id}",
            json={"description": "Updated desc"},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated desc"

    def test_edit_blocked_with_bids(self, client, create_user, create_item, create_bid):
        """Edit blocked when bids exist."""
        seller, token = create_user(username="seller", password="password123")
        buyer, _ = create_user(username="buyer", password="password123")
        item = create_item(seller_id=seller.id, starting_price=10.0)
        create_bid(item_id=item.id, user_id=buyer.id, amount=15.0)

        resp = client.patch(
            f"/auction/items/{item.id}",
            json={"title": "Sneaky Edit"},
            headers=auth_header(token),
        )
        assert resp.status_code == 400

    def test_edit_by_non_seller_blocked(self, client, create_user, create_item):
        """Only the seller can edit their item."""
        seller, _ = create_user(username="seller", password="password123")
        _, other_token = create_user(username="other", password="password123")
        item = create_item(seller_id=seller.id)

        resp = client.patch(
            f"/auction/items/{item.id}",
            json={"title": "Hacked Title"},
            headers=auth_header(other_token),
        )
        assert resp.status_code == 403

    def test_edit_closed_item_blocked(self, client, create_user, create_item):
        """Cannot edit a closed item."""
        seller, token = create_user(username="seller", password="password123")
        item = create_item(seller_id=seller.id, status="closed")

        resp = client.patch(
            f"/auction/items/{item.id}",
            json={"title": "Whatever"},
            headers=auth_header(token),
        )
        assert resp.status_code == 400

    def test_edit_nonexistent_item(self, client, create_user):
        """Editing a non-existent item returns 404."""
        _, token = create_user(username="seller", password="password123")
        resp = client.patch(
            "/auction/items/99999",
            json={"title": "Nope"},
            headers=auth_header(token),
        )
        assert resp.status_code == 404
