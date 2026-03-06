"""
TC12 – Receipt includes shipping time, distinguishes standard vs expedited.
"""
from datetime import datetime, timedelta, timezone

from tests.conftest import VALID_PAYMENT, auth_header


class TestReceipt:
    """UC6 – Buyer receives a receipt after payment."""

    def _setup_and_pay(self, client, db, create_user, create_item, create_bid, expedited=False):
        """Create users, item, bid, close auction, pay. Returns the receipt response."""
        seller, seller_token = create_user(username="seller", password="password123")
        buyer, buyer_token = create_user(username="buyer", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(
            seller_id=seller.id,
            starting_price=10.0,
            end_time=past,
            highest_bidder_id=buyer.id,
            current_price=50.0,
            shipping_time_days=7,
            expedited_shipping_cost=20.0,
        )
        create_bid(item_id=item.id, user_id=buyer.id, amount=50.0)

        # Close
        client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(seller_token),
        )

        payment = {**VALID_PAYMENT, "expedited_shipping": expedited}
        pay_resp = client.post(
            f"/payment/items/{item.id}/pay",
            json=payment,
            headers=auth_header(buyer_token),
        )
        return pay_resp, buyer_token

    def test_receipt_standard_shipping(self, client, db, create_user, create_item, create_bid):
        """TC12 – Standard shipping receipt."""
        pay_resp, _ = self._setup_and_pay(client, db, create_user, create_item, create_bid, expedited=False)
        assert pay_resp.status_code == 200
        receipt = pay_resp.json()
        assert receipt["shipping_time_days"] == 7
        assert receipt["expedited_shipping"] is False
        assert receipt["amount_paid"] == 50.0  # no expedited surcharge

    def test_receipt_expedited_shipping(self, client, db, create_user, create_item, create_bid):
        """TC12 – Expedited shipping adds surcharge to amount."""
        pay_resp, _ = self._setup_and_pay(client, db, create_user, create_item, create_bid, expedited=True)
        assert pay_resp.status_code == 200
        receipt = pay_resp.json()
        assert receipt["expedited_shipping"] is True
        assert receipt["amount_paid"] == 70.0  # 50 + 20 expedited

    def test_receipt_contains_required_fields(self, client, db, create_user, create_item, create_bid):
        """Receipt has all expected fields."""
        pay_resp, _ = self._setup_and_pay(client, db, create_user, create_item, create_bid)
        receipt = pay_resp.json()
        for field in ("order_id", "item_id", "item_title", "amount_paid",
                       "shipping_address", "shipping_time_days",
                       "expedited_shipping", "paid_at", "message"):
            assert field in receipt, f"Missing field: {field}"

    def test_get_receipt_by_order_id(self, client, db, create_user, create_item, create_bid):
        """Fetch a stored receipt by order id."""
        pay_resp, buyer_token = self._setup_and_pay(client, db, create_user, create_item, create_bid)
        order_id = pay_resp.json()["order_id"]

        resp = client.get(f"/payment/orders/{order_id}/receipt", headers=auth_header(buyer_token))
        assert resp.status_code == 200
        assert resp.json()["order_id"] == order_id

    def test_receipt_forbidden_for_other_user(self, client, db, create_user, create_item, create_bid):
        """Another user cannot fetch someone else's receipt."""
        pay_resp, _ = self._setup_and_pay(client, db, create_user, create_item, create_bid)
        order_id = pay_resp.json()["order_id"]
        _, other_token = create_user(username="other", password="password123")

        resp = client.get(f"/payment/orders/{order_id}/receipt", headers=auth_header(other_token))
        assert resp.status_code == 403
