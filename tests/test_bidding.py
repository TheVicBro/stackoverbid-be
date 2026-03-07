from datetime import datetime, timedelta, timezone

from tests.conftest import auth_header


class TestValidBid:

    def test_bid_success(self, client, create_user, create_item):
        """A valid bid (higher than current price) is accepted."""
        seller, _ = create_user(username="seller", password="password123")
        buyer, token = create_user(username="buyer", password="password123")
        item = create_item(seller_id=seller.id, starting_price=10.0)

        resp = client.post(
            f"/auction/items/{item.id}/bid",
            json={"amount": 15.0},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["amount"] == 15.0
        assert body["user_id"] == buyer.id
        assert body["item_id"] == item.id

    def test_bid_updates_current_price(self, client, create_user, create_item):
        """After a successful bid the item's current_price is updated."""
        seller, _ = create_user(username="seller", password="password123")
        _, token = create_user(username="buyer", password="password123")
        item = create_item(seller_id=seller.id, starting_price=10.0)

        client.post(
            f"/auction/items/{item.id}/bid",
            json={"amount": 20.0},
            headers=auth_header(token),
        )
        resp = client.get(f"/catalogue/items/{item.id}", headers=auth_header(token))
        assert resp.json()["current_price"] == 20.0

    def test_multiple_bids_increasing(self, client, create_user, create_item):
        """Multiple bids from different users, each higher than the last."""
        seller, _ = create_user(username="seller", password="password123")
        _, token_a = create_user(username="alice", password="password123")
        _, token_b = create_user(username="bob", password="password123")
        item = create_item(seller_id=seller.id, starting_price=10.0)

        resp1 = client.post(f"/auction/items/{item.id}/bid", json={"amount": 15.0}, headers=auth_header(token_a))
        assert resp1.status_code == 200

        resp2 = client.post(f"/auction/items/{item.id}/bid", json={"amount": 20.0}, headers=auth_header(token_b))
        assert resp2.status_code == 200


class TestInvalidBid:

    def test_bid_lower_than_current(self, client, create_user, create_item):
        """Bid amount <= current price is rejected."""
        seller, _ = create_user(username="seller", password="password123")
        _, token = create_user(username="buyer", password="password123")
        item = create_item(seller_id=seller.id, starting_price=100.0)

        resp = client.post(
            f"/auction/items/{item.id}/bid",
            json={"amount": 50.0},
            headers=auth_header(token),
        )
        assert resp.status_code == 400

    def test_bid_equal_to_current(self, client, create_user, create_item):
        """Bid exactly equal to current price is rejected."""
        seller, _ = create_user(username="seller", password="password123")
        _, token = create_user(username="buyer", password="password123")
        item = create_item(seller_id=seller.id, starting_price=100.0)

        resp = client.post(
            f"/auction/items/{item.id}/bid",
            json={"amount": 100.0},
            headers=auth_header(token),
        )
        assert resp.status_code == 400

    def test_seller_cannot_bid_own_item(self, client, create_user, create_item):
        """Seller cannot bid on their own item."""
        seller, token = create_user(username="seller", password="password123")
        item = create_item(seller_id=seller.id, starting_price=10.0)

        resp = client.post(
            f"/auction/items/{item.id}/bid",
            json={"amount": 20.0},
            headers=auth_header(token),
        )
        assert resp.status_code == 403

    def test_bid_on_closed_item(self, client, create_user, create_item):
        """Cannot bid on a closed auction."""
        seller, _ = create_user(username="seller", password="password123")
        _, token = create_user(username="buyer", password="password123")
        item = create_item(seller_id=seller.id, starting_price=10.0, status="closed")

        resp = client.post(
            f"/auction/items/{item.id}/bid",
            json={"amount": 20.0},
            headers=auth_header(token),
        )
        assert resp.status_code == 400

    def test_bid_on_expired_item(self, client, create_user, create_item):
        """Cannot bid on an expired auction (end_time in the past)."""
        seller, _ = create_user(username="seller", password="password123")
        _, token = create_user(username="buyer", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, starting_price=10.0, end_time=past)

        resp = client.post(
            f"/auction/items/{item.id}/bid",
            json={"amount": 20.0},
            headers=auth_header(token),
        )
        assert resp.status_code == 400

    def test_bid_on_nonexistent_item(self, client, create_user):
        """Bidding on a non-existent item returns 404."""
        _, token = create_user(username="buyer", password="password123")
        resp = client.post(
            "/auction/items/99999/bid",
            json={"amount": 20.0},
            headers=auth_header(token),
        )
        assert resp.status_code == 404
