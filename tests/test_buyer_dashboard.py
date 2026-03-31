from datetime import datetime, timedelta, timezone

from tests.conftest import VALID_PAYMENT, auth_header


class TestBuyerDashboard:
    def test_dashboard_requires_auth(self, client):
        resp = client.get("/auction/my/dashboard")
        assert resp.status_code == 401

    def test_dashboard_empty_when_no_activity(self, client, create_user):
        _, token = create_user()
        resp = client.get("/auction/my/dashboard", headers=auth_header(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["active_bids"] == []
        assert body["won_awaiting_payment"] == []
        assert body["other_auctions_i_bid_on"] == []
        assert body["purchases"] == []

    def test_active_bid_and_won_sections(self, client, create_user, create_item, create_bid):
        seller, _ = create_user(username="seller", password="password123")
        buyer, buyer_token = create_user(username="buyer", password="password123")
        future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)
        live = create_item(seller_id=seller.id, title="Live Thing", end_time=future, status="active")
        create_bid(item_id=live.id, user_id=buyer.id, amount=25.0)

        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)
        closed = create_item(
            seller_id=seller.id,
            title="Closed Win",
            end_time=past,
            status="closed",
            highest_bidder_id=buyer.id,
            current_price=40.0,
        )
        create_bid(item_id=closed.id, user_id=buyer.id, amount=40.0)

        resp = client.get("/auction/my/dashboard", headers=auth_header(buyer_token))
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["active_bids"]) == 1
        assert body["active_bids"][0]["item_id"] == live.id
        assert len(body["won_awaiting_payment"]) == 1
        assert body["won_awaiting_payment"][0]["item_id"] == closed.id

    def test_purchases_after_payment(self, client, create_user, create_item, create_bid):
        seller, _ = create_user(username="seldash", password="password123")
        buyer, buyer_token = create_user(username="buydash", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(
            seller_id=seller.id,
            title="Bought Via Pay",
            end_time=past,
            status="closed",
            highest_bidder_id=buyer.id,
            current_price=18.0,
        )
        create_bid(item_id=item.id, user_id=buyer.id, amount=18.0)
        pay = client.post(
            f"/payment/items/{item.id}/pay",
            json=VALID_PAYMENT,
            headers=auth_header(buyer_token),
        )
        assert pay.status_code == 200

        dash = client.get("/auction/my/dashboard", headers=auth_header(buyer_token))
        assert dash.status_code == 200
        purchases = dash.json()["purchases"]
        assert len(purchases) == 1
        assert purchases[0]["item_id"] == item.id
        assert purchases[0]["amount_paid"] >= 18.0
