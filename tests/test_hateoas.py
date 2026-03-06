"""
HATEOAS link tests – verify every API response includes contextual hypermedia links.
"""
from datetime import datetime, timedelta, timezone

from tests.conftest import VALID_PAYMENT, auth_header


class TestAuthLinks:
    """Auth endpoints return navigational links."""

    def test_signup_has_login_link(self, client):
        payload = {
            "username": "newuser",
            "password": "password123",
            "first_name": "A",
            "last_name": "B",
            "address": "addr",
        }
        resp = client.post("/auth/signup", json=payload)
        assert resp.status_code == 200
        links = resp.json()["links"]
        rels = {link["rel"] for link in links}
        assert "login" in rels
        login_link = next(l for l in links if l["rel"] == "login")
        assert login_link["href"] == "/auth/login"
        assert login_link["method"] == "POST"

    def test_login_has_navigation_links(self, client, create_user):
        create_user(username="alice", password="password123")
        resp = client.post("/auth/login", json={"username": "alice", "password": "password123"})
        assert resp.status_code == 200
        links = resp.json()["links"]
        rels = {link["rel"] for link in links}
        assert "catalogue" in rels
        assert "create_item" in rels
        assert "notifications" in rels


class TestCatalogueLinks:
    """Catalogue endpoints return self/bid links."""

    def test_item_list_has_links(self, client, create_user, create_item):
        seller, _ = create_user(username="seller", password="password123")
        _, token = create_user(username="buyer", password="password123")
        item = create_item(seller_id=seller.id, title="Widget")

        resp = client.get("/catalogue/items", headers=auth_header(token))
        items = resp.json()
        assert len(items) == 1
        links = items[0]["links"]
        rels = {link["rel"] for link in links}
        assert "self" in rels
        assert "bid" in rels
        self_link = next(l for l in links if l["rel"] == "self")
        assert self_link["href"] == f"/catalogue/items/{item.id}"

    def test_item_detail_has_links(self, client, create_user, create_item):
        seller, _ = create_user(username="seller", password="password123")
        _, token = create_user(username="buyer", password="password123")
        item = create_item(seller_id=seller.id)

        resp = client.get(f"/catalogue/items/{item.id}", headers=auth_header(token))
        links = resp.json()["links"]
        rels = {link["rel"] for link in links}
        assert "self" in rels
        assert "bid" in rels
        assert "catalogue" in rels


class TestAuctionLinks:
    """Auction endpoints return context-appropriate links."""

    def test_create_item_has_links(self, client, create_user):
        _, token = create_user(username="seller", password="password123")
        future = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        payload = {"title": "New", "description": "desc", "starting_price": 10.0, "end_time": future}
        resp = client.post("/auction/items", json=payload, headers=auth_header(token))
        assert resp.status_code == 200
        links = resp.json()["links"]
        rels = {link["rel"] for link in links}
        assert "self" in rels
        assert "edit" in rels
        assert "bid" in rels

    def test_edit_item_has_links(self, client, create_user, create_item):
        seller, token = create_user(username="seller", password="password123")
        item = create_item(seller_id=seller.id)
        resp = client.patch(
            f"/auction/items/{item.id}",
            json={"title": "Updated"},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        rels = {link["rel"] for link in resp.json()["links"]}
        assert "self" in rels
        assert "bid" in rels

    def test_place_bid_has_item_link(self, client, create_user, create_item):
        seller, _ = create_user(username="seller", password="password123")
        _, token = create_user(username="buyer", password="password123")
        item = create_item(seller_id=seller.id, starting_price=10.0)

        resp = client.post(
            f"/auction/items/{item.id}/bid",
            json={"amount": 15.0},
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        links = resp.json()["links"]
        assert any(l["rel"] == "item" and l["href"] == f"/catalogue/items/{item.id}" for l in links)


class TestPaymentLinks:
    """Payment/receipt endpoints return self + catalogue links."""

    def _close_and_pay(self, client, create_user, create_item, create_bid):
        seller, seller_token = create_user(username="seller", password="password123")
        buyer, buyer_token = create_user(username="buyer", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(
            seller_id=seller.id, starting_price=10.0, end_time=past,
            highest_bidder_id=buyer.id, current_price=20.0,
        )
        create_bid(item_id=item.id, user_id=buyer.id, amount=20.0)
        client.post(f"/notifications/items/{item.id}/broadcast-end", headers=auth_header(seller_token))
        resp = client.post(f"/payment/items/{item.id}/pay", json=VALID_PAYMENT, headers=auth_header(buyer_token))
        return resp, buyer_token

    def test_receipt_has_self_and_catalogue_links(self, client, create_user, create_item, create_bid):
        resp, _ = self._close_and_pay(client, create_user, create_item, create_bid)
        assert resp.status_code == 200
        rels = {l["rel"] for l in resp.json()["links"]}
        assert "self" in rels
        assert "catalogue" in rels

    def test_get_receipt_has_links(self, client, create_user, create_item, create_bid):
        resp, buyer_token = self._close_and_pay(client, create_user, create_item, create_bid)
        order_id = resp.json()["order_id"]
        receipt_resp = client.get(f"/payment/orders/{order_id}/receipt", headers=auth_header(buyer_token))
        assert receipt_resp.status_code == 200
        rels = {l["rel"] for l in receipt_resp.json()["links"]}
        assert "self" in rels
        assert "catalogue" in rels


class TestNotificationLinks:
    """Notification list returns item link + pay link for winners."""

    def test_winner_notification_has_pay_link(self, client, create_user, create_item, create_bid):
        seller, seller_token = create_user(username="seller", password="password123")
        buyer, buyer_token = create_user(username="buyer", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, starting_price=10.0, end_time=past)
        create_bid(item_id=item.id, user_id=buyer.id, amount=20.0)

        client.post(f"/notifications/items/{item.id}/broadcast-end", headers=auth_header(seller_token))

        resp = client.get("/notifications/", headers=auth_header(buyer_token))
        notifs = resp.json()
        assert len(notifs) == 1
        rels = {l["rel"] for l in notifs[0]["links"]}
        assert "item" in rels
        assert "pay" in rels

    def test_loser_notification_has_item_link_only(self, client, create_user, create_item, create_bid):
        seller, seller_token = create_user(username="seller", password="password123")
        buyer1, buyer1_token = create_user(username="loser", password="password123")
        buyer2, _ = create_user(username="winner", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, starting_price=10.0, end_time=past)
        create_bid(item_id=item.id, user_id=buyer1.id, amount=15.0)
        create_bid(item_id=item.id, user_id=buyer2.id, amount=25.0)

        client.post(f"/notifications/items/{item.id}/broadcast-end", headers=auth_header(seller_token))

        resp = client.get("/notifications/", headers=auth_header(buyer1_token))
        notifs = resp.json()
        assert len(notifs) == 1
        rels = {l["rel"] for l in notifs[0]["links"]}
        assert "item" in rels
        assert "pay" not in rels

    def test_broadcast_end_has_links(self, client, create_user, create_item, create_bid):
        """broadcast-end response includes item and notifications links."""
        seller, seller_token = create_user(username="seller", password="password123")
        buyer, _ = create_user(username="buyer", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, starting_price=10.0, end_time=past)
        create_bid(item_id=item.id, user_id=buyer.id, amount=20.0)

        resp = client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(seller_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "links" in body
        rels = {l["rel"] for l in body["links"]}
        assert "item" in rels
        assert "notifications" in rels
