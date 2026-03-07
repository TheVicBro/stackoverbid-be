from tests.conftest import auth_header


class TestBrowseItems:

    def test_list_all_active_items(self, client, create_user, create_item):
        """Returns all active items with prices."""
        seller, _ = create_user(username="seller", password="password123")
        buyer, token = create_user(username="buyer", password="password123")
        create_item(seller_id=seller.id, title="Widget A", starting_price=25.0)
        create_item(seller_id=seller.id, title="Widget B", starting_price=50.0)

        resp = client.get("/catalogue/items", headers=auth_header(token))
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 2
        # Each item must expose price info
        for item in items:
            assert "current_price" in item
            assert "starting_price" in item

    def test_search_by_keyword(self, client, create_user, create_item):
        """Search returns only items whose title matches the keyword."""
        seller, _ = create_user(username="seller", password="password123")
        _, token = create_user(username="buyer", password="password123")
        create_item(seller_id=seller.id, title="Vintage Guitar")
        create_item(seller_id=seller.id, title="Gaming Console")

        resp = client.get("/catalogue/items", params={"keyword": "guitar"}, headers=auth_header(token))
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert "guitar" in items[0]["title"].lower()

    def test_search_no_results(self, client, create_user, create_item):
        """Keyword that matches nothing returns empty list."""
        seller, _ = create_user(username="seller", password="password123")
        _, token = create_user(username="buyer", password="password123")
        create_item(seller_id=seller.id, title="Widget")

        resp = client.get("/catalogue/items", params={"keyword": "nonexistent"}, headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_closed_items_excluded(self, client, create_user, create_item):
        """Browse only returns active items, not closed."""
        seller, _ = create_user(username="seller", password="password123")
        _, token = create_user(username="buyer", password="password123")
        create_item(seller_id=seller.id, title="Active Item", status="active")
        create_item(seller_id=seller.id, title="Closed Item", status="closed")

        resp = client.get("/catalogue/items", headers=auth_header(token))
        items = resp.json()
        assert len(items) == 1
        assert items[0]["title"] == "Active Item"


class TestItemDetails:

    def test_get_item_by_id(self, client, create_user, create_item):
        """Select item returns full detail."""
        seller, _ = create_user(username="seller", password="password123")
        _, token = create_user(username="buyer", password="password123")
        item = create_item(seller_id=seller.id, title="Rare Coin", description="Very rare")

        resp = client.get(f"/catalogue/items/{item.id}", headers=auth_header(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Rare Coin"
        assert body["description"] == "Very rare"
        assert "starting_price" in body
        assert "current_price" in body
        assert "end_time" in body

    def test_get_item_not_found(self, client, create_user):
        """Non-existent item id returns 404."""
        _, token = create_user(username="buyer", password="password123")
        resp = client.get("/catalogue/items/99999", headers=auth_header(token))
        assert resp.status_code == 404
