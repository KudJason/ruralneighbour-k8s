import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from uuid import uuid4
from app.services.paypal_service import PayPalService
from app.models.payment import PaymentStatus, PaymentMethod
from app.schemas.payment import PaymentProcess


class TestPayPalService:

    @pytest.fixture
    def mock_db(self):
        return Mock()

    @pytest.fixture
    def sample_paypal_payment_process(self):
        return PaymentProcess(
            request_id=uuid4(),
            payer_id=uuid4(),
            payee_id=uuid4(),
            amount=Decimal("100.00"),
            payment_method=PaymentMethod.PAYPAL,
            payment_token="paypal_token",
        )

    @patch("app.services.paypal_service.paypalrestsdk")
    def test_process_payment_success(
        self, mock_paypal_sdk, mock_db, sample_paypal_payment_process
    ):
        """Test successful PayPal payment creation"""
        # Mock PayPal payment creation
        mock_paypal_payment = Mock()
        mock_paypal_payment.id = "PAY-123456789"
        mock_paypal_payment.create.return_value = True
        mock_paypal_payment.links = [
            Mock(rel="approval_url", href="https://paypal.com/approve"),
            Mock(rel="execute", href="https://paypal.com/execute"),
        ]
        mock_paypal_sdk.Payment.return_value = mock_paypal_payment

        # Mock database operations
        mock_payment = Mock()
        mock_payment.payment_id = uuid4()
        mock_payment.payment_status = PaymentStatus.PROCESSING

        with patch(
            "app.services.paypal_service.create_payment", return_value=mock_payment
        ), patch("app.services.paypal_service.update_payment"), patch(
            "app.services.paypal_service.create_payment_history"
        ), patch(
            "app.services.paypal_service.get_payment_by_id", return_value=mock_payment
        ):

            result = PayPalService.process_payment(
                mock_db, sample_paypal_payment_process
            )

            assert result["status"] == "created"
            assert result["paypal_payment_id"] == "PAY-123456789"
            assert "approval_url" in result
            assert result["approval_url"] == "https://paypal.com/approve"

    @patch("app.services.paypal_service.paypalrestsdk")
    def test_process_payment_failure(
        self, mock_paypal_sdk, mock_db, sample_paypal_payment_process
    ):
        """Test PayPal payment creation failure"""
        # Mock PayPal payment creation failure
        mock_paypal_payment = Mock()
        mock_paypal_payment.create.return_value = False
        mock_paypal_payment.error = "Payment creation failed"
        mock_paypal_sdk.Payment.return_value = mock_paypal_payment

        # Mock database operations
        mock_payment = Mock()
        mock_payment.payment_id = uuid4()

        with patch(
            "app.services.paypal_service.create_payment", return_value=mock_payment
        ), patch("app.services.paypal_service.update_payment"), patch(
            "app.services.paypal_service.create_payment_history"
        ), patch(
            "app.services.paypal_service.EventPublisher.publish_payment_failed"
        ):

            with pytest.raises(Exception) as exc_info:
                PayPalService.process_payment(mock_db, sample_paypal_payment_process)

            assert "PayPal payment creation failed" in str(exc_info.value)

    @patch("app.services.paypal_service.paypalrestsdk")
    def test_execute_payment_success(self, mock_paypal_sdk, mock_db):
        """Test successful PayPal payment execution"""
        payment_id = str(uuid4())
        payer_id = "PAYER123"

        # Mock payment retrieval
        mock_payment = Mock()
        mock_payment.payment_id = uuid4()
        mock_payment.request_id = uuid4()
        mock_payment.amount = Decimal("100.00")
        mock_payment.transaction_id = "PAY-123456789"

        # Mock PayPal payment execution
        mock_paypal_payment = Mock()
        mock_paypal_payment.execute.return_value = True
        mock_paypal_sdk.Payment.find.return_value = mock_paypal_payment

        with patch(
            "app.services.paypal_service.get_payment_by_id", return_value=mock_payment
        ), patch("app.services.paypal_service.update_payment"), patch(
            "app.services.paypal_service.create_payment_history"
        ), patch(
            "app.services.paypal_service.EventPublisher.publish_payment_processed"
        ):

            result = PayPalService.execute_payment(mock_db, payment_id, payer_id)

            assert result == mock_payment
            mock_paypal_payment.execute.assert_called_once_with({"payer_id": payer_id})

    @patch("app.services.paypal_service.paypalrestsdk")
    def test_execute_payment_failure(self, mock_paypal_sdk, mock_db):
        """Test PayPal payment execution failure"""
        payment_id = str(uuid4())
        payer_id = "PAYER123"

        # Mock payment retrieval
        mock_payment = Mock()
        mock_payment.payment_id = uuid4()
        mock_payment.request_id = uuid4()
        mock_payment.amount = Decimal("100.00")
        mock_payment.transaction_id = "PAY-123456789"

        # Mock PayPal payment execution failure
        mock_paypal_payment = Mock()
        mock_paypal_payment.execute.return_value = False
        mock_paypal_payment.error = "Execution failed"
        mock_paypal_sdk.Payment.find.return_value = mock_paypal_payment

        with patch(
            "app.services.paypal_service.get_payment_by_id", return_value=mock_payment
        ), patch("app.services.paypal_service.update_payment"), patch(
            "app.services.paypal_service.create_payment_history"
        ), patch(
            "app.services.paypal_service.EventPublisher.publish_payment_failed"
        ):

            with pytest.raises(Exception) as exc_info:
                PayPalService.execute_payment(mock_db, payment_id, payer_id)

            assert "PayPal payment execution failed" in str(exc_info.value)

    def test_cancel_payment_success(self, mock_db):
        """Test successful PayPal payment cancellation"""
        payment_id = str(uuid4())

        # Mock payment retrieval
        mock_payment = Mock()
        mock_payment.payment_id = uuid4()

        with patch(
            "app.services.paypal_service.get_payment_by_id", return_value=mock_payment
        ), patch("app.services.paypal_service.update_payment"), patch(
            "app.services.paypal_service.create_payment_history"
        ):

            result = PayPalService.cancel_payment(mock_db, payment_id)

            assert result == mock_payment

    def test_cancel_payment_not_found(self, mock_db):
        """Test PayPal payment cancellation when payment not found"""
        payment_id = str(uuid4())

        with patch("app.services.paypal_service.get_payment_by_id", return_value=None):

            with pytest.raises(Exception) as exc_info:
                PayPalService.cancel_payment(mock_db, payment_id)

            assert "Payment not found" in str(exc_info.value)
