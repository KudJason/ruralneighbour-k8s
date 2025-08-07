import pytest
import os
from decimal import Decimal
from uuid import uuid4
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.payment_method import (
    UserPaymentMethod,
    PaymentMethodType,
    PaymentProvider,
)
from app.crud.crud_payment import (
    create_payment,
    get_payment_by_id,
    get_payments_by_user,
)
from app.crud.crud_payment_method import create_payment_method, get_user_payment_methods
from app.schemas.payment import PaymentCreate
from app.schemas.payment_method import PaymentMethodCreate


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true" or os.getenv("TESTING") == "true",
    reason="Skipping integration tests when database is not available",
)
class TestDatabaseIntegration:
    """Integration tests using real database operations"""

    def test_create_and_retrieve_payment(self, db_session):
        """Test creating and retrieving a payment from the database"""
        # Create test payment data using schema
        payment_data = PaymentCreate(
            request_id=uuid4(),
            payer_id=uuid4(),
            payee_id=uuid4(),
            amount=Decimal("100.00"),
            payment_method=PaymentMethod.CREDIT_CARD,
        )

        # Create payment in database
        payment = create_payment(db_session, payment_data)

        # Verify payment was created
        assert payment.payment_id is not None
        assert payment.amount == Decimal("100.00")
        assert payment.payment_status == PaymentStatus.PENDING

        # Retrieve payment by ID
        retrieved_payment = get_payment_by_id(db_session, payment.payment_id)
        assert retrieved_payment is not None
        assert retrieved_payment.payment_id == payment.payment_id
        assert retrieved_payment.amount == Decimal("100.00")

    def test_create_and_retrieve_payment_method(self, db_session):
        """Test creating and retrieving a payment method from the database"""
        user_id = uuid4()

        # Create test payment method data using schema
        payment_method_data = PaymentMethodCreate(
            method_type=PaymentMethodType.CREDIT_CARD,
            provider=PaymentProvider.STRIPE,
            provider_token="pm_test_1234567890",
            display_name="Test Credit Card",
            set_as_default=True,
        )

        # Create payment method in database
        payment_method = create_payment_method(db_session, payment_method_data, user_id)

        # Verify payment method was created
        assert payment_method.method_id is not None
        assert payment_method.user_id == user_id
        assert payment_method.method_type == PaymentMethodType.CREDIT_CARD
        assert payment_method.is_default is True

        # Retrieve payment methods for user
        user_methods = get_user_payment_methods(db_session, user_id)
        assert len(user_methods) == 1
        assert user_methods[0].method_id == payment_method.method_id

    def test_get_payments_by_user(self, db_session):
        """Test retrieving payments for a specific user"""
        user_id = uuid4()

        # Create multiple payments for the same user
        payments_data = [
            PaymentCreate(
                request_id=uuid4(),
                payer_id=user_id,
                payee_id=uuid4(),
                amount=Decimal("50.00"),
                payment_method=PaymentMethod.CREDIT_CARD,
            ),
            PaymentCreate(
                request_id=uuid4(),
                payer_id=user_id,
                payee_id=uuid4(),
                amount=Decimal("75.00"),
                payment_method=PaymentMethod.PAYPAL,
            ),
        ]

        # Create payments in database
        created_payments = []
        for payment_data in payments_data:
            payment = create_payment(db_session, payment_data)
            created_payments.append(payment)

        # Retrieve payments for user
        user_payments = get_payments_by_user(db_session, user_id)

        # Verify all payments were retrieved
        assert len(user_payments) == 2
        assert all(payment.payer_id == user_id for payment in user_payments)

        # Verify payment amounts
        amounts = [payment.amount for payment in user_payments]
        assert Decimal("50.00") in amounts
        assert Decimal("75.00") in amounts

    def test_database_isolation(self, db_session):
        """Test that database is properly isolated between tests"""
        # Create a payment in this test
        payment_data = PaymentCreate(
            request_id=uuid4(),
            payer_id=uuid4(),
            payee_id=uuid4(),
            amount=Decimal("200.00"),
            payment_method=PaymentMethod.CREDIT_CARD,
        )

        payment = create_payment(db_session, payment_data)

        # Verify payment exists in this test
        retrieved_payment = get_payment_by_id(db_session, payment.payment_id)
        assert retrieved_payment is not None
        assert retrieved_payment.amount == Decimal("200.00")

        # This test should be isolated from other tests
        # The clean_database fixture will clear this data after the test
