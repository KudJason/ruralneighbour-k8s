import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from decimal import Decimal
from uuid import uuid4
from app.main import app
from app.models.payment import PaymentStatus, PaymentMethod, RefundStatus

client = TestClient(app)


class TestPaymentAPI:

    @pytest.fixture
    def sample_payment_process_data(self):
        return {
            "request_id": str(uuid4()),
            "payer_id": str(uuid4()),
            "payee_id": str(uuid4()),
            "amount": "100.00",
            "payment_method": "credit_card",
            "payment_token": "tok_visa",
        }

    @pytest.fixture
    def sample_refund_data(self):
        return {
            "payment_id": str(uuid4()),
            "amount": "50.00",
            "refund_reason": "Customer request",
        }

    @patch("app.api.v1.endpoints.payments.PaymentService.process_payment")
    @patch("app.api.v1.endpoints.payments.get_db")
    def test_process_payment_success(
        self, mock_get_db, mock_process_payment, sample_payment_process_data
    ):
        """Test successful payment processing endpoint"""
        # Mock database dependency
        mock_get_db.return_value = Mock()

        # Mock payment service response
        mock_payment = Mock()
        mock_payment.payment_id = uuid4()
        mock_payment.payment_status = PaymentStatus.SUCCESS
        mock_payment.transaction_id = "ch_1234567890"
        mock_process_payment.return_value = mock_payment

        response = client.post(
            "/api/v1/payments/process", json=sample_payment_process_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["payment_id"] == str(mock_payment.payment_id)
        assert data["status"] == "success"
        assert data["transaction_id"] == "ch_1234567890"
        assert data["message"] == "Payment processed successfully"

    @patch("app.api.v1.endpoints.payments.PaymentService.process_payment")
    @patch("app.api.v1.endpoints.payments.get_db")
    def test_process_payment_failure(
        self, mock_get_db, mock_process_payment, sample_payment_process_data
    ):
        """Test payment processing failure endpoint"""
        # Mock database dependency
        mock_get_db.return_value = Mock()

        # Mock payment service exception
        mock_process_payment.side_effect = Exception("Payment failed")

        response = client.post(
            "/api/v1/payments/process", json=sample_payment_process_data
        )

        assert response.status_code == 500
        data = response.json()
        assert "Payment processing failed" in data["detail"]

    @patch("app.api.v1.endpoints.payments.PaymentService.get_payment_history")
    @patch("app.api.v1.endpoints.payments.get_db")
    def test_get_payment_history(self, mock_get_db, mock_get_history):
        """Test getting payment history endpoint"""
        # Mock database dependency
        mock_get_db.return_value = Mock()

        # Mock payment service response with proper data structure
        from datetime import datetime
        from decimal import Decimal

        mock_payment_1 = {
            "payment_id": uuid4(),
            "request_id": uuid4(),
            "payer_id": uuid4(),
            "payee_id": uuid4(),
            "amount": Decimal("100.00"),
            "payment_status": PaymentStatus.SUCCESS,
            "payment_method": PaymentMethod.CREDIT_CARD,
            "transaction_id": "ch_1234567890",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        mock_payment_2 = {
            "payment_id": uuid4(),
            "request_id": uuid4(),
            "payer_id": uuid4(),
            "payee_id": uuid4(),
            "amount": Decimal("50.00"),
            "payment_status": PaymentStatus.SUCCESS,
            "payment_method": PaymentMethod.PAYPAL,
            "transaction_id": "paypal_tx_123",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        mock_result = {
            "payments": [mock_payment_1, mock_payment_2],
            "total_count": 2,
            "page": 1,
            "page_size": 20,
        }
        mock_get_history.return_value = mock_result

        user_id = str(uuid4())
        response = client.get(
            f"/api/v1/payments/history?user_id={user_id}&page=1&page_size=20"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert data["page"] == 1
        assert data["page_size"] == 20

    @patch("app.api.v1.endpoints.payments.PaymentService.process_refund")
    @patch("app.api.v1.endpoints.payments.get_db")
    def test_process_refund_success(
        self, mock_get_db, mock_process_refund, sample_refund_data
    ):
        """Test successful refund processing endpoint"""
        # Mock database dependency
        mock_get_db.return_value = Mock()

        # Mock refund service response
        mock_result = {
            "refund_id": str(uuid4()),
            "status": RefundStatus.COMPLETED,
            "message": "Refund processed successfully",
        }
        mock_process_refund.return_value = mock_result

        payment_id = str(uuid4())
        admin_id = str(uuid4())

        response = client.post(
            f"/api/v1/payments/{payment_id}/refund?admin_id={admin_id}",
            json=sample_refund_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["refund_id"] == mock_result["refund_id"]
        assert data["status"] == "completed"
        assert data["message"] == "Refund processed successfully"

    def test_process_payment_invalid_data(self):
        """Test payment processing with invalid data"""
        invalid_data = {
            "request_id": "invalid-uuid",
            "payer_id": str(uuid4()),
            "payee_id": str(uuid4()),
            "amount": "-100.00",  # Negative amount
            "payment_method": "invalid_method",
            "payment_token": "tok_visa",
        }

        response = client.post("/api/v1/payments/process", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_get_payment_history_missing_user_id(self):
        """Test getting payment history without user_id"""
        response = client.get("/api/v1/payments/history")

        assert response.status_code == 422  # Validation error

    def test_process_refund_missing_admin_id(self):
        """Test refund processing without admin_id"""
        refund_data = {
            "payment_id": str(uuid4()),
            "amount": "50.00",
            "refund_reason": "Customer request",
        }

        payment_id = str(uuid4())
        response = client.post(
            f"/api/v1/payments/{payment_id}/refund", json=refund_data
        )

        assert response.status_code == 422  # Validation error

    @patch("app.api.v1.endpoints.payments.PayPalService.execute_payment")
    @patch("app.api.v1.endpoints.payments.get_db")
    def test_execute_paypal_payment_success(self, mock_get_db, mock_execute_payment):
        """Test successful PayPal payment execution endpoint"""
        # Mock database dependency
        mock_get_db.return_value = Mock()

        # Mock payment execution response
        mock_payment = Mock()
        mock_payment.payment_id = uuid4()
        mock_payment.payment_status = PaymentStatus.SUCCESS
        mock_payment.transaction_id = "PAY-123456789"
        mock_execute_payment.return_value = mock_payment

        payment_id = str(uuid4())
        payer_id = "PAYER123"

        response = client.post(
            f"/api/v1/payments/paypal/execute?payment_id={payment_id}&payer_id={payer_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["payment_id"] == str(mock_payment.payment_id)
        assert data["status"] == "success"
        assert data["transaction_id"] == "PAY-123456789"
        assert data["message"] == "PayPal payment executed successfully"

    @patch("app.api.v1.endpoints.payments.PayPalService.cancel_payment")
    @patch("app.api.v1.endpoints.payments.get_db")
    def test_cancel_paypal_payment_success(self, mock_get_db, mock_cancel_payment):
        """Test successful PayPal payment cancellation endpoint"""
        # Mock database dependency
        mock_get_db.return_value = Mock()

        # Mock payment cancellation response
        mock_payment = Mock()
        mock_payment.payment_id = uuid4()
        mock_payment.payment_status = PaymentStatus.CANCELLED
        mock_payment.transaction_id = "PAY-123456789"
        mock_cancel_payment.return_value = mock_payment

        payment_id = str(uuid4())

        response = client.post(
            f"/api/v1/payments/paypal/cancel?payment_id={payment_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["payment_id"] == str(mock_payment.payment_id)
        assert data["status"] == "cancelled"
        assert data["transaction_id"] == "PAY-123456789"
        assert data["message"] == "PayPal payment cancelled"
