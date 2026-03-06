from datetime import datetime, timedelta, timezone

from tests.conftest import auth_header


class TestAuctionLifecycle:

    def test_broadcast_end_closes_auction(self, client, create_user, create_item, create_bid):
        """Seller broadcasts end, item status becomes 'closed'."""
        seller, seller_token = create_user(username="seller", password="password123")
        buyer, buyer_token = create_user(username="buyer", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, starting_price=10.0, end_time=past)
        create_bid(item_id=item.id, user_id=buyer.id, amount=20.0)

        resp = client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(seller_token),
        )
        assert resp.status_code == 200

        # Item should now be closed - verify by attempting a bid
        bid_resp = client.post(
            f"/auction/items/{item.id}/bid",
            json={"amount": 30.0},
            headers=auth_header(buyer_token),
        )
        assert bid_resp.status_code == 400
        assert "closed" in bid_resp.json()["detail"].lower() or "not" in bid_resp.json()["detail"].lower()

    def test_broadcast_end_only_by_seller(self, client, create_user, create_item):
        """Only the seller can close their auction."""
        seller, _ = create_user(username="seller", password="password123")
        _, other_token = create_user(username="other", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, end_time=past)

        resp = client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(other_token),
        )
        assert resp.status_code == 403

    def test_broadcast_end_before_end_time(self, client, create_user, create_item):
        """Cannot close an auction before its end time."""
        seller, token = create_user(username="seller", password="password123")
        future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=2)
        item = create_item(seller_id=seller.id, end_time=future)

        resp = client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(token),
        )
        assert resp.status_code == 400

    def test_no_bids_auction_still_closes(self, client, create_user, create_item):
        """An auction with zero bids can still be closed after end time."""
        seller, token = create_user(username="seller", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, end_time=past)

        resp = client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
