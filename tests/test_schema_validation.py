"""
Edge-case schema validation tests – PaymentRequest, UserCreate, ItemCreate.
"""
import pytest
from pydantic import ValidationError

from app.schemas.schemas import PaymentRequest, UserCreate, ItemCreate
from datetime import datetime, timedelta, timezone


class TestPaymentSchemaEdgeCases:
    def test_luhn_valid_visa(self):
        PaymentRequest(
            credit_card_number="4111111111111111",
            name_on_card="Test",
            expiration_date="12/30",
            security_code="123",
        )

    def test_luhn_valid_with_spaces(self):
        req = PaymentRequest(
            credit_card_number="4111 1111 1111 1111",
            name_on_card="Test",
            expiration_date="12/30",
            security_code="123",
        )
        # Validator strips spaces
        assert req.credit_card_number == "4111111111111111"

    def test_luhn_valid_with_hyphens(self):
        req = PaymentRequest(
            credit_card_number="4111-1111-1111-1111",
            name_on_card="Test",
            expiration_date="12/30",
            security_code="123",
        )
        assert req.credit_card_number == "4111111111111111"

    def test_luhn_invalid(self):
        with pytest.raises(ValidationError):
            PaymentRequest(
                credit_card_number="1234567890123",
                name_on_card="Test",
                expiration_date="12/30",
                security_code="123",
            )

    def test_card_with_letters_rejected(self):
        with pytest.raises(ValidationError):
            PaymentRequest(
                credit_card_number="4111ABCD11111111",
                name_on_card="Test",
                expiration_date="12/30",
                security_code="123",
            )

    def test_cvv_3_digits(self):
        PaymentRequest(
            credit_card_number="4111111111111111",
            name_on_card="Test",
            expiration_date="12/30",
            security_code="123",
        )

    def test_cvv_4_digits(self):
        PaymentRequest(
            credit_card_number="4111111111111111",
            name_on_card="Test",
            expiration_date="12/30",
            security_code="1234",
        )

    def test_cvv_letters_rejected(self):
        with pytest.raises(ValidationError):
            PaymentRequest(
                credit_card_number="4111111111111111",
                name_on_card="Test",
                expiration_date="12/30",
                security_code="12a",
            )

    def test_cvv_5_digits_rejected(self):
        with pytest.raises(ValidationError):
            PaymentRequest(
                credit_card_number="4111111111111111",
                name_on_card="Test",
                expiration_date="12/30",
                security_code="12345",
            )

    def test_expiry_mm_yy_slash(self):
        PaymentRequest(
            credit_card_number="4111111111111111",
            name_on_card="Test",
            expiration_date="12/30",
            security_code="123",
        )

    def test_expiry_mm_yy_dash(self):
        PaymentRequest(
            credit_card_number="4111111111111111",
            name_on_card="Test",
            expiration_date="12-30",
            security_code="123",
        )

    def test_expiry_single_digit_month_rejected(self):
        """'1/30' must be '01/30'."""
        with pytest.raises(ValidationError):
            PaymentRequest(
                credit_card_number="4111111111111111",
                name_on_card="Test",
                expiration_date="1/30",
                security_code="123",
            )

    def test_expiry_expired(self):
        with pytest.raises(ValidationError):
            PaymentRequest(
                credit_card_number="4111111111111111",
                name_on_card="Test",
                expiration_date="01/20",
                security_code="123",
            )

    def test_expiry_month_13(self):
        with pytest.raises(ValidationError):
            PaymentRequest(
                credit_card_number="4111111111111111",
                name_on_card="Test",
                expiration_date="13/30",
                security_code="123",
            )

    def test_empty_name_on_card(self):
        with pytest.raises(ValidationError):
            PaymentRequest(
                credit_card_number="4111111111111111",
                name_on_card="",
                expiration_date="12/30",
                security_code="123",
            )


class TestUserCreateSchema:
    def test_username_too_short(self):
        with pytest.raises(ValidationError):
            UserCreate(username="ab", password="password123", first_name="A", last_name="B", address="addr")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            UserCreate(username="validuser", password="short", first_name="A", last_name="B", address="addr")

    def test_empty_username(self):
        with pytest.raises(ValidationError):
            UserCreate(username="", password="password123", first_name="A", last_name="B", address="addr")

    def test_empty_password(self):
        with pytest.raises(ValidationError):
            UserCreate(username="validuser", password="", first_name="A", last_name="B", address="addr")

    def test_valid_user(self):
        user = UserCreate(username="validuser", password="password123", first_name="A", last_name="B", address="addr")
        assert user.username == "validuser"


class TestItemCreateSchema:
    def test_empty_title(self):
        with pytest.raises(ValidationError):
            ItemCreate(
                title="",
                description="desc",
                starting_price=10.0,
                end_time=datetime.now(timezone.utc) + timedelta(days=1),
            )

    def test_negative_price(self):
        with pytest.raises(ValidationError):
            ItemCreate(
                title="Valid Title",
                description="desc",
                starting_price=-1.0,
                end_time=datetime.now(timezone.utc) + timedelta(days=1),
            )

    def test_end_time_in_past(self):
        with pytest.raises(ValidationError):
            ItemCreate(
                title="Valid Title",
                description="desc",
                starting_price=10.0,
                end_time=datetime.now(timezone.utc) - timedelta(hours=1),
            )

    def test_valid_item(self):
        item = ItemCreate(
            title="Valid Title",
            description="desc",
            starting_price=10.0,
            end_time=datetime.now(timezone.utc) + timedelta(days=1),
        )
        assert item.title == "Valid Title"
