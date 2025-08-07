import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from uuid import uuid4
from app.services.payment_method_service import PaymentMethodService
from app.models.payment_method import PaymentMethodType, PaymentProvider
from app.schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodUpdate,
    QuickPaymentRequest,
)


class TestPaymentMethodService:

    @pytest.fixture
    def mock_db(self):
        return Mock()

    @pytest.fixture
    def sample_user_id(self):
        return uuid4()

    @pytest.fixture
    def sample_payment_method_create(self):
        return PaymentMethodCreate(
            method_type=PaymentMethodType.CREDIT_CARD,
            provider=PaymentProvider.STRIPE,
            provider_token="pm_1234567890",
            display_name="My Credit Card",
            set_as_default=True,
        )

    @pytest.fixture
    def sample_quick_payment_request(self):
        return QuickPaymentRequest(
            request_id=uuid4(),
            payee_id=uuid4(),
            amount="100.00",
            method_id=uuid4(),
            description="Test payment",
        )

    @patch("app.services.payment_method_service.stripe")
    def test_save_stripe_payment_method_success(
        self, mock_stripe, mock_db, sample_user_id, sample_payment_method_create
    ):
        """Test successful Stripe payment method saving"""
        # Mock Stripe customer creation
        mock_customer = Mock()
        mock_customer.id = "cus_1234567890"
        mock_stripe.Customer.create.return_value = mock_customer

        # Mock payment method attachment
        mock_stripe.PaymentMethod.attach.return_value = None

        # Mock payment method retrieval
        mock_pm = Mock()
        mock_pm.type = "card"
        mock_pm.card = Mock()
        mock_pm.card.brand = "visa"
        mock_pm.card.last4 = "4242"
        mock_pm.card.exp_month = 12
        mock_pm.card.exp_year = 2025
        mock_stripe.PaymentMethod.retrieve.return_value = mock_pm

        # Mock database operations
        mock_payment_method = Mock()
        mock_payment_method.method_id = uuid4()

        with patch(
            "app.services.payment_method_service.create_payment_method",
            return_value=mock_payment_method,
        ), patch(
            "app.services.payment_method_service.EventPublisher.publish_payment_method_saved"
        ):

            result = PaymentMethodService.save_payment_method(
                mock_db, sample_user_id, sample_payment_method_create
            )

            assert result == mock_payment_method
            mock_stripe.Customer.create.assert_called_once()
            mock_stripe.PaymentMethod.attach.assert_called_once()

    def test_save_paypal_payment_method_success(self, mock_db, sample_user_id):
        """Test successful PayPal payment method saving"""
        paypal_payment_method = PaymentMethodCreate(
            method_type=PaymentMethodType.PAYPAL,
            provider=PaymentProvider.PAYPAL,
            provider_token="agreement_123",
            display_name="My PayPal",
            set_as_default=False,
        )

        # Mock database operations
        mock_payment_method = Mock()
        mock_payment_method.method_id = uuid4()

        with patch(
            "app.services.payment_method_service.create_payment_method",
            return_value=mock_payment_method,
        ), patch(
            "app.services.payment_method_service.EventPublisher.publish_payment_method_saved"
        ):

            result = PaymentMethodService.save_payment_method(
                mock_db, sample_user_id, paypal_payment_method
            )

            assert result == mock_payment_method

    def test_get_user_payment_methods(self, mock_db, sample_user_id):
        """Test getting user payment methods"""
        mock_methods = [Mock(), Mock()]

        with patch(
            "app.services.payment_method_service.get_user_payment_methods",
            return_value=mock_methods,
        ), patch(
            "app.services.payment_method_service.count_user_payment_methods",
            return_value=2,
        ):

            result = PaymentMethodService.get_user_payment_methods(
                mock_db, sample_user_id
            )

            assert result["payment_methods"] == mock_methods
            assert result["total_count"] == 2

    def test_update_payment_method_success(self, mock_db, sample_user_id):
        """Test successful payment method update"""
        method_id = uuid4()
        update_data = PaymentMethodUpdate(display_name="Updated Card")

        mock_payment_method = Mock()
        mock_payment_method.method_id = method_id

        with patch(
            "app.services.payment_method_service.update_payment_method",
            return_value=mock_payment_method,
        ):

            result = PaymentMethodService.update_payment_method(
                mock_db, method_id, sample_user_id, update_data
            )

            assert result == mock_payment_method

    def test_update_payment_method_not_found(self, mock_db, sample_user_id):
        """Test payment method update when method not found"""
        method_id = uuid4()
        update_data = PaymentMethodUpdate(display_name="Updated Card")

        with patch(
            "app.services.payment_method_service.update_payment_method",
            return_value=None,
        ):

            with pytest.raises(Exception) as exc_info:
                PaymentMethodService.update_payment_method(
                    mock_db, method_id, sample_user_id, update_data
                )

            assert "Payment method not found" in str(exc_info.value)

    def test_set_default_payment_method_success(self, mock_db, sample_user_id):
        """Test successful default payment method setting"""
        method_id = uuid4()

        mock_payment_method = Mock()
        mock_payment_method.method_id = method_id
        mock_payment_method.is_default = True

        with patch(
            "app.services.payment_method_service.set_default_payment_method",
            return_value=mock_payment_method,
        ):

            result = PaymentMethodService.set_default_payment_method(
                mock_db, method_id, sample_user_id
            )

            assert result == mock_payment_method
            assert result.is_default == True

    def test_delete_payment_method_success(self, mock_db, sample_user_id):
        """Test successful payment method deletion"""
        method_id = uuid4()

        with patch(
            "app.services.payment_method_service.delete_payment_method",
            return_value=True,
        ), patch(
            "app.services.payment_method_service.EventPublisher.publish_payment_method_deleted"
        ):

            result = PaymentMethodService.delete_payment_method(
                mock_db, method_id, sample_user_id
            )

            assert result == True

    @patch("app.services.payment_method_service.stripe")
    def test_process_quick_payment_stripe_success(
        self, mock_stripe, mock_db, sample_user_id, sample_quick_payment_request
    ):
        """Test successful quick payment with Stripe"""
        # Mock saved payment method
        mock_payment_method = Mock()
        mock_payment_method.method_id = sample_quick_payment_request.method_id
        mock_payment_method.provider = PaymentProvider.STRIPE
        mock_payment_method.provider_method_id = "cus_123:pm_456"

        # Mock Stripe payment intent
        mock_intent = Mock()
        mock_intent.id = "pi_1234567890"
        mock_intent.status = "succeeded"
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        with patch(
            "app.services.payment_method_service.get_payment_method_by_id",
            return_value=mock_payment_method,
        ), patch(
            "app.services.payment_method_service.create_payment_method_usage"
        ), patch(
            "app.services.payment_method_service.EventPublisher.publish_payment_method_used"
        ):

            result = PaymentMethodService.process_quick_payment(
                mock_db, sample_user_id, sample_quick_payment_request
            )

            assert result["status"] == "success"
            assert result["transaction_id"] == "pi_1234567890"
            mock_stripe.PaymentIntent.create.assert_called_once()

    def test_process_quick_payment_method_not_found(
        self, mock_db, sample_user_id, sample_quick_payment_request
    ):
        """Test quick payment when payment method not found"""
        with patch(
            "app.services.payment_method_service.get_payment_method_by_id",
            return_value=None,
        ):

            with pytest.raises(Exception) as exc_info:
                PaymentMethodService.process_quick_payment(
                    mock_db, sample_user_id, sample_quick_payment_request
                )

            assert "Payment method not found" in str(exc_info.value)

    def test_process_quick_payment_paypal_success(
        self, mock_db, sample_user_id, sample_quick_payment_request
    ):
        """Test successful quick payment with PayPal"""
        # Mock saved payment method
        mock_payment_method = Mock()
        mock_payment_method.method_id = sample_quick_payment_request.method_id
        mock_payment_method.provider = PaymentProvider.PAYPAL
        mock_payment_method.provider_method_id = "agreement_123"

        with patch(
            "app.services.payment_method_service.get_payment_method_by_id",
            return_value=mock_payment_method,
        ), patch(
            "app.services.payment_method_service.create_payment_method_usage"
        ), patch(
            "app.services.payment_method_service.EventPublisher.publish_payment_method_used"
        ):

            result = PaymentMethodService.process_quick_payment(
                mock_db, sample_user_id, sample_quick_payment_request
            )

            assert result["status"] == "success"
            assert "paypal" in result["transaction_id"]

    def test_unsupported_provider_save(self, mock_db, sample_user_id):
        """Test saving payment method with unsupported provider"""
        # Since Pydantic validates enums at creation time, we test by
        # mocking an unsupported provider in the service logic
        valid_method = PaymentMethodCreate(
            method_type=PaymentMethodType.CREDIT_CARD,
            provider=PaymentProvider.STRIPE,
            provider_token="token_123",
            display_name="Test Card",
            set_as_default=False,
        )

        # Mock the provider to be unsupported after creation
        with patch.object(valid_method, "provider", "unsupported_provider"):
            with pytest.raises(Exception) as exc_info:
                PaymentMethodService.save_payment_method(
                    mock_db, sample_user_id, valid_method
                )

            assert "Unsupported payment provider" in str(exc_info.value)
