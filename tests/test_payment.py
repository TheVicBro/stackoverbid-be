"""
TC9  – Winning bidder can pay for item.
TC10 – Non-winning bidder is blocked from paying.
TC11 – Missing or invalid payment fields are rejected (422).
"""
from datetime import datetime, timedelta, timezone

from tests.conftest import VALID_PAYMENT, auth_header


class TestPaymentSuccess:
    """UC5 – winning bidder pays for the item."""

    def _close_auction(self, client, db, create_user, create_item, create_bid):
        """Helper: create seller + buyer, make item, bid, close auction. Returns (item, buyer_token)."""
        seller, seller_token = create_user(username="seller", password="password123")
        buyer, buyer_token = create_user(username="buyer", password="password123")
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
        item = create_item(
            seller_id=seller.id,
            starting_price=10.0,
            end_time=past,
            highest_bidder_id=buyer.id,
            current_price=20.0,
        )
        create_bid(item_id=item.id, user_id=buyer.id, amount=20.0)
        # Close via broadcast
        client.post(
            f"/notifications/items/{item.id}/broadcast-end",
            headers=auth_header(seller_token),
        )
        return item, buyer_token, seller_token

    def test_winning_bidder_pays(self, client, db, create_user, create_item, create_bid):
        """TC9 – Winning bidder can submit payment and receives receipt."""
        item, buyer_token, _ = self._close_auction(client, db, create_user, create_item, create_bid)

        resp = client.post(
            f"/payment/items/{item.id}/pay",
            json=VALID_PAYMENT,
            headers=auth_header(buyer_token),
        )
        assert resp.status_code == 200
        receipt = resp.json()
        assert receipt["item_id"] == item.id
        assert receipt["amount_paid"] == 20.0
        assert "shipping_address" in receipt

    def test_non_winner_cannot_pay(self, client, db, create_user, create_item, create_bid):
        """TC10 – A user who is NOT the highest bidder cannot pay."""
        item, _, seller_token = self._close_auction(client, db, create_user, create_item, create_bid)
        _, other_token = create_user(username="other", password="password123")

        resp = client.post(
            f"/payment/items/{item.id}/pay",
            json=VALID_PAYMENT,
            headers=auth_header(other_token),
        )
        assert resp.status_code == 403

    def test_cannot_pay_active_item(self, client, create_user, create_item):
        """Payment blocked while auction is still active."""
        seller, _ = create_user(username="seller", password="password123")
        buyer, token = create_user(username="buyer", password="password123")
        item = create_item(seller_id=seller.id, starting_price=10.0)

        resp = client.post(
            f"/payment/items/{item.id}/pay",
            json=VALID_PAYMENT,
            headers=auth_header(token),
        )
        assert resp.status_code == 400

    def test_double_payment_blocked(self, client, db, create_user, create_item, create_bid):
        """Paying for the same item twice is blocked (status ≠ 'closed' after first pay)."""
        item, buyer_token, _ = self._close_auction(client, db, create_user, create_item, create_bid)

        first = client.post(
            f"/payment/items/{item.id}/pay",
            json=VALID_PAYMENT,
            headers=auth_header(buyer_token),
        )
        assert first.status_code == 200

        second = client.post(
            f"/payment/items/{item.id}/pay",
            json=VALID_PAYMENT,
            headers=auth_header(buyer_token),
        )
        assert second.status_code == 400


class TestPaymentValidation:
    """TC11 – Missing or invalid payment fields are rejected."""

    def test_empty_card_number(self, client, create_user):
        _, token = create_user()
        payment = {**VALID_PAYMENT, "credit_card_number": ""}
        resp = client.post("/payment/items/1/pay", json=payment, headers=auth_header(token))
        assert resp.status_code == 422

    def test_invalid_card_number(self, client, create_user):
        _, token = create_user()
        payment = {**VALID_PAYMENT, "credit_card_number": "1234567890123"}
        resp = client.post("/payment/items/1/pay", json=payment, headers=auth_header(token))
        assert resp.status_code == 422

    def test_card_with_letters(self, client, create_user):
        _, token = create_user()
        payment = {**VALID_PAYMENT, "credit_card_number": "4111-ABCD-1111-1111"}
        resp = client.post("/payment/items/1/pay", json=payment, headers=auth_header(token))
        assert resp.status_code == 422

    def test_empty_name_on_card(self, client, create_user):
        _, token = create_user()
        payment = {**VALID_PAYMENT, "name_on_card": ""}
        resp = client.post("/payment/items/1/pay", json=payment, headers=auth_header(token))
        assert resp.status_code == 422

    def test_invalid_expiry_format(self, client, create_user):
        _, token = create_user()
        payment = {**VALID_PAYMENT, "expiration_date": "1/2"}
        resp = client.post("/payment/items/1/pay", json=payment, headers=auth_header(token))
        assert resp.status_code == 422

    def test_expired_card(self, client, create_user):
        _, token = create_user()
        payment = {**VALID_PAYMENT, "expiration_date": "01/20"}
        resp = client.post("/payment/items/1/pay", json=payment, headers=auth_header(token))
        assert resp.status_code == 422

    def test_cvv_too_short(self, client, create_user):
        _, token = create_user()
        payment = {**VALID_PAYMENT, "security_code": "12"}
        resp = client.post("/payment/items/1/pay", json=payment, headers=auth_header(token))
        assert resp.status_code == 422

    def test_cvv_with_letters(self, client, create_user):
        _, token = create_user()
        payment = {**VALID_PAYMENT, "security_code": "12a"}
        resp = client.post("/payment/items/1/pay", json=payment, headers=auth_header(token))
        assert resp.status_code == 422

    def test_missing_fields(self, client, create_user):
        _, token = create_user()
        resp = client.post("/payment/items/1/pay", json={}, headers=auth_header(token))
        assert resp.status_code == 422
