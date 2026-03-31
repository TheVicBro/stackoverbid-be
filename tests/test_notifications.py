from datetime import datetime, timedelta, timezone

from tests.conftest import auth_header


class TestNotifications:
    def test_notifications_created_on_auction_end(self, client, create_user, create_item, create_bid):
        """When an auction ends, notifications are created for all bidders."""
        seller, seller_token = create_user(username="seller", password="password123")
        buyer1, buyer1_token = create_user(username="buyer1", password="password123")
        buyer2, buyer2_token = create_user(username="buyer2", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, starting_price=10.0, end_time=past)

        create_bid(item_id=item.id, user_id=buyer1.id, amount=15.0)
        create_bid(item_id=item.id, user_id=buyer2.id, amount=20.0)

        resp = client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(seller_token),
        )
        assert resp.status_code == 200

        # Both bidders should have notifications
        resp1 = client.get("/notifications/", headers=auth_header(buyer1_token))
        assert resp1.status_code == 200
        assert len(resp1.json()) >= 1

        resp2 = client.get("/notifications/", headers=auth_header(buyer2_token))
        assert resp2.status_code == 200
        assert len(resp2.json()) >= 1

    def test_winner_flag_correct(self, client, create_user, create_item, create_bid):
        """The highest bidder's notification has is_highest_bidder=True."""
        seller, seller_token = create_user(username="seller", password="password123")
        buyer1, buyer1_token = create_user(username="loser", password="password123")
        buyer2, buyer2_token = create_user(username="winner", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, starting_price=10.0, end_time=past)

        create_bid(item_id=item.id, user_id=buyer1.id, amount=15.0)
        create_bid(item_id=item.id, user_id=buyer2.id, amount=25.0)

        client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(seller_token),
        )

        # Winner
        notifs = client.get("/notifications/", headers=auth_header(buyer2_token)).json()
        winner_notifs = [n for n in notifs if n["is_highest_bidder"]]
        assert len(winner_notifs) == 1

        # Loser
        notifs = client.get("/notifications/", headers=auth_header(buyer1_token)).json()
        loser_notifs = [n for n in notifs if not n["is_highest_bidder"]]
        assert len(loser_notifs) == 1

    def test_list_notifications_empty(self, client, create_user):
        """User with no notifications gets an empty list."""
        _, token = create_user(username="lonely", password="password123")
        resp = client.get("/notifications/", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_notifications_scoped_to_user(self, client, create_user, create_item, create_bid):
        """A user who didn't bid on an item does NOT receive a notification for it."""
        seller, seller_token = create_user(username="seller", password="password123")
        bidder, _ = create_user(username="bidder", password="password123")
        bystander, bystander_token = create_user(username="bystander", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, starting_price=10.0, end_time=past)
        create_bid(item_id=item.id, user_id=bidder.id, amount=15.0)

        client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(seller_token),
        )

        resp = client.get("/notifications/", headers=auth_header(bystander_token))
        assert resp.json() == []

    def test_delete_own_notification(self, client, create_user, create_item, create_bid):
        seller, seller_token = create_user(username="sdel", password="password123")
        buyer, buyer_token = create_user(username="bdel", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, starting_price=10.0, end_time=past)
        create_bid(item_id=item.id, user_id=buyer.id, amount=20.0)
        client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(seller_token),
        )
        notifs = client.get("/notifications/", headers=auth_header(buyer_token)).json()
        assert len(notifs) >= 1
        nid = notifs[0]["id"]
        del_resp = client.delete(f"/notifications/{nid}", headers=auth_header(buyer_token))
        assert del_resp.status_code == 204
        after = client.get("/notifications/", headers=auth_header(buyer_token)).json()
        assert not any(n["id"] == nid for n in after)

    def test_delete_other_users_notification_forbidden(self, client, create_user, create_item, create_bid):
        seller, seller_token = create_user(username="s2del", password="password123")
        buyer, buyer_token = create_user(username="b2del", password="password123")
        other, other_token = create_user(username="odel", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, starting_price=10.0, end_time=past)
        create_bid(item_id=item.id, user_id=buyer.id, amount=20.0)
        client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(seller_token),
        )
        notifs = client.get("/notifications/", headers=auth_header(buyer_token)).json()
        nid = notifs[0]["id"]
        del_resp = client.delete(f"/notifications/{nid}", headers=auth_header(other_token))
        assert del_resp.status_code == 404

    def test_delete_all_notifications(self, client, create_user, create_item, create_bid):
        seller, seller_token = create_user(username="s3del", password="password123")
        buyer, buyer_token = create_user(username="b3del", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, starting_price=10.0, end_time=past)
        create_bid(item_id=item.id, user_id=buyer.id, amount=20.0)
        client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(seller_token),
        )
        assert len(client.get("/notifications/", headers=auth_header(buyer_token)).json()) >= 1
        clr = client.delete("/notifications/all", headers=auth_header(buyer_token))
        assert clr.status_code == 204
        assert client.get("/notifications/", headers=auth_header(buyer_token)).json() == []

    def test_post_dismiss_notification(self, client, create_user, create_item, create_bid):
        seller, seller_token = create_user(username="spost", password="password123")
        buyer, buyer_token = create_user(username="bpost", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, starting_price=10.0, end_time=past)
        create_bid(item_id=item.id, user_id=buyer.id, amount=20.0)
        client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(seller_token),
        )
        notifs = client.get("/notifications/", headers=auth_header(buyer_token)).json()
        nid = notifs[0]["id"]
        r = client.post(
            "/notifications/dismiss",
            json={"notification_id": nid},
            headers=auth_header(buyer_token),
        )
        assert r.status_code == 204
        assert client.get("/notifications/", headers=auth_header(buyer_token)).json() == []

    def test_post_dismiss_all(self, client, create_user, create_item, create_bid):
        seller, seller_token = create_user(username="spa", password="password123")
        buyer, buyer_token = create_user(username="bpa", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(seller_id=seller.id, starting_price=10.0, end_time=past)
        create_bid(item_id=item.id, user_id=buyer.id, amount=20.0)
        client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(seller_token),
        )
        r = client.post("/notifications/dismiss-all", headers=auth_header(buyer_token))
        assert r.status_code == 204
        assert client.get("/notifications/", headers=auth_header(buyer_token)).json() == []
