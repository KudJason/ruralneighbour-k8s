import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from uuid import uuid4
from app.services.payment_service import PaymentService
from app.models.payment import PaymentStatus, PaymentMethod, RefundStatus
from app.schemas.payment import PaymentProcess, RefundCreate


class TestPaymentService:

    @pytest.fixture
    def mock_db(self):
        return Mock()

    @pytest.fixture
    def sample_payment_process(self):
        return PaymentProcess(
            request_id=uuid4(),
            payer_id=uuid4(),
            payee_id=uuid4(),
            amount=Decimal("100.00"),
            payment_method=PaymentMethod.CREDIT_CARD,
            payment_token="tok_visa",
        )

    @pytest.fixture
    def sample_refund_create(self):
        return RefundCreate(
            payment_id=uuid4(),
            amount=Decimal("50.00"),
            refund_reason="Customer request",
        )

    @patch("app.services.payment_service.stripe")
    def test_process_stripe_payment_success(
        self, mock_stripe, mock_db, sample_payment_process
    ):
        """Test successful Stripe payment processing"""
        # Mock Stripe charge
        mock_charge = Mock()
        mock_charge.id = "ch_1234567890"
        mock_stripe.Charge.create.return_value = mock_charge

        # Mock database operations
        mock_payment = Mock()
        mock_payment.payment_id = uuid4()
        mock_payment.payment_status = PaymentStatus.SUCCESS
        mock_payment.transaction_id = "ch_1234567890"

        with patch(
            "app.services.payment_service.create_payment", return_value=mock_payment
        ), patch(
            "app.services.payment_service.update_payment", return_value=mock_payment
        ), patch(
            "app.services.payment_service.get_payment_by_id", return_value=mock_payment
        ), patch(
            "app.services.payment_service.create_payment_history"
        ), patch(
            "app.services.payment_service.EventPublisher.publish_payment_processed"
        ):

            result = PaymentService.process_payment(mock_db, sample_payment_process)

            assert result.payment_status == PaymentStatus.SUCCESS
            assert result.transaction_id == "ch_1234567890"

    @patch("app.services.payment_service.PayPalService.process_payment")
    def test_process_paypal_payment_success(self, mock_paypal_service, mock_db):
        """Test successful PayPal payment processing"""
        # Create PayPal payment request
        paypal_payment_request = PaymentProcess(
            request_id=uuid4(),
            payer_id=uuid4(),
            payee_id=uuid4(),
            amount=Decimal("100.00"),
            payment_method=PaymentMethod.PAYPAL,
            payment_token="paypal_token",
        )

        # Mock PayPal service response
        mock_paypal_response = {
            "payment_id": str(uuid4()),
            "paypal_payment_id": "PAY-123456789",
            "approval_url": "https://www.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-123",
            "status": "created",
        }
        mock_paypal_service.return_value = mock_paypal_response

        result = PaymentService.process_payment(mock_db, paypal_payment_request)

        assert result["status"] == "created"
        assert "approval_url" in result
        mock_paypal_service.assert_called_once_with(mock_db, paypal_payment_request)

    def test_process_payment_unsupported_method(self, mock_db):
        """Test payment processing with unsupported method"""
        # Create payment request with unsupported method
        unsupported_payment_request = PaymentProcess(
            request_id=uuid4(),
            payer_id=uuid4(),
            payee_id=uuid4(),
            amount=Decimal("100.00"),
            payment_method=PaymentMethod.DIGITAL_WALLET,  # Not supported yet
            payment_token="token",
        )

        with pytest.raises(Exception) as exc_info:
            PaymentService.process_payment(mock_db, unsupported_payment_request)

        assert "Unsupported payment method" in str(exc_info.value)

    @patch("app.services.payment_service.stripe")
    def test_process_payment_failure(
        self, mock_stripe, mock_db, sample_payment_process
    ):
        """Test payment processing failure"""
        # Mock Stripe error
        mock_stripe.error.CardError = Exception
        mock_stripe.Charge.create.side_effect = Exception("Card declined")

        with patch("app.services.payment_service.create_payment"), patch(
            "app.services.payment_service.update_payment"
        ), patch("app.services.payment_service.create_payment_history"), patch(
            "app.services.payment_service.EventPublisher.publish_payment_failed"
        ):

            with pytest.raises(Exception):
                PaymentService.process_payment(mock_db, sample_payment_process)

    def test_get_payment_history(self, mock_db):
        """Test getting payment history"""
        user_id = uuid4()
        page = 1
        page_size = 20

        mock_payments = [Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.count.return_value = 2

        with patch(
            "app.services.payment_service.get_payments_by_user",
            return_value=mock_payments,
        ):
            result = PaymentService.get_payment_history(
                mock_db, user_id, page, page_size
            )

            assert result["payments"] == mock_payments
            assert result["total_count"] == 2
            assert result["page"] == page
            assert result["page_size"] == page_size

    @patch("app.services.payment_service.stripe")
    def test_process_refund_success(self, mock_stripe, mock_db, sample_refund_create):
        """Test successful refund processing"""
        # Mock payment
        mock_payment = Mock()
        mock_payment.payment_status = PaymentStatus.SUCCESS
        mock_payment.amount = Decimal("100.00")
        mock_payment.transaction_id = "ch_1234567890"
        mock_payment.request_id = uuid4()

        # Mock refund
        mock_refund = Mock()
        mock_refund.refund_id = uuid4()

        # Mock Stripe refund
        mock_stripe_refund = Mock()
        mock_stripe.Refund.create.return_value = mock_stripe_refund

        admin_id = uuid4()

        with patch(
            "app.services.payment_service.get_payment_by_id", return_value=mock_payment
        ), patch(
            "app.services.payment_service.create_refund", return_value=mock_refund
        ), patch(
            "app.services.payment_service.update_refund"
        ), patch(
            "app.services.payment_service.EventPublisher.publish_payment_refunded"
        ), patch.object(
            mock_db, "query"
        ) as mock_query:
            # Mock the refund query to return empty list (no existing refunds)
            mock_query.return_value.filter.return_value.all.return_value = []

            result = PaymentService.process_refund(
                mock_db, uuid4(), sample_refund_create, admin_id
            )

            assert result["status"] == RefundStatus.COMPLETED
            assert "successfully" in result["message"]

    def test_create_pending_payment(self, mock_db):
        """Test creating a pending payment for service request"""
        request_id = uuid4()
        payer_id = uuid4()
        payee_id = uuid4()
        amount = Decimal("150.00")

        mock_payment = Mock()
        mock_payment.payment_id = uuid4()

        with patch(
            "app.services.payment_service.create_payment", return_value=mock_payment
        ), patch("app.services.payment_service.create_payment_history"):

            result = PaymentService.create_pending_payment(
                mock_db, request_id, payer_id, payee_id, amount
            )

            assert result == mock_payment
