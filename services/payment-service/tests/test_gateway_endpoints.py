import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from app.main import app


client = TestClient(app)


class TestStripeGateway:

    @patch("app.api.v1.endpoints.payments.stripe")
    def test_create_payment_intent_without_method(self, mock_stripe):
        mock_intent = Mock()
        mock_intent.id = "pi_123"
        mock_intent.status = "requires_payment_method"
        mock_intent.client_secret = "secret_abc"
        mock_intent.amount = 1299
        mock_intent.currency = "usd"
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        res = client.post(
            "/api/v1/payments/stripe/payment-intent",
            json={"amount": 1299, "currency": "USD", "description": "test"},
        )

        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "pi_123"
        assert data["status"] == "requires_payment_method"
        assert data["client_secret"] == "secret_abc"
        assert data["amount"] == 1299
        assert data["currency"] == "usd"

    @patch("app.api.v1.endpoints.payments.stripe")
    def test_create_payment_intent_with_method(self, mock_stripe):
        mock_intent = Mock()
        mock_intent.id = "pi_456"
        mock_intent.status = "succeeded"
        mock_intent.client_secret = None
        mock_intent.amount = 500
        mock_intent.currency = "usd"
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        res = client.post(
            "/api/v1/payments/stripe/payment-intent",
            json={
                "amount": 500,
                "currency": "usd",
                "description": "desc",
                "payment_method_id": "pm_123",
            },
        )

        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "pi_456"
        assert data["status"] == "succeeded"
        assert data["client_secret"] is None
        assert data["amount"] == 500

    @patch("app.api.v1.endpoints.payments.stripe")
    def test_attach_method(self, mock_stripe):
        mock_customer = Mock()
        mock_customer.id = "cus_123"
        mock_pm = Mock()
        mock_pm.id = "pm_abc"
        mock_pm.type = "card"
        mock_pm.card = Mock(last4="4242")
        mock_stripe.Customer.create.return_value = mock_customer
        mock_stripe.PaymentMethod.attach.return_value = mock_pm

        res = client.post(
            "/api/v1/payments/stripe/attach-method",
            json={"payment_method_id": "pm_abc", "make_default": True},
        )

        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "pm_abc"
        assert data["type"] == "card"
        assert data["last_four"] == "4242"
        assert data["is_default"] is True


class TestPayPalGateway:

    def test_paypal_create_order(self):
        with patch("app.services.paypal_service.paypalrestsdk") as mock_sdk:
            mock_payment = Mock()
            mock_payment.id = "PAY-1"
            mock_payment.create.return_value = True
            mock_payment.links = [Mock(rel="approval_url", href="https://paypal/approve")]
            mock_sdk.Payment.return_value = mock_payment

            res = client.post(
                "/api/v1/payments/paypal/create-order",
                json={
                    "amount": 1299,
                    "currency": "USD",
                    "description": "test",
                    "return_url": "https://return",
                    "cancel_url": "https://cancel",
                },
            )

            assert res.status_code == 200
            data = res.json()
            assert data["id"] == "PAY-1"
            assert data["status"] == "CREATED"
            assert data["approve_url"] == "https://paypal/approve"

    def test_paypal_capture_order(self):
        with patch("app.services.paypal_service.paypalrestsdk") as mock_sdk:
            mock_payment = Mock()
            mock_payment.execute.return_value = True
            mock_payment.state = "completed"
            mock_payment.id = "PAY-1"
            mock_sdk.Payment.find.return_value = mock_payment

            res = client.post(
                "/api/v1/payments/paypal/capture/PAY-1",
                json={"payer_id": "PAYER123"},
            )

            assert res.status_code == 200
            data = res.json()
            assert data["id"] == mock_payment.id if hasattr(mock_payment, "id") else "PAY-1"
            assert data["status"] == "COMPLETED"


class TestMethodsAndTransactions:

    def test_create_method_via_payments_prefix(self):
        with patch("app.api.v1.endpoints.payments.PaymentMethodService.save_payment_method") as mock_save:
            mock_method = Mock()
            mock_method.method_id = "m1"
            mock_method.method_type = "card"
            mock_method.provider = "stripe"
            mock_method.last_four = "4242"
            mock_method.is_default = True
            mock_method.is_active = True
            mock_save.return_value = mock_method

            res = client.post(
                "/api/v1/payments/methods",
                json={"type": "card", "details": {"payment_method_id": "pm_abc", "brand": "VISA"}, "is_default": True},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["is_default"] is True

    def test_update_method_via_payments_prefix(self):
        with patch("app.api.v1.endpoints.payments.PaymentMethodService.update_payment_method") as mock_update, \
             patch("app.api.v1.endpoints.payments.PaymentMethodService.set_default_payment_method") as mock_set_default:
            mock_method = Mock()
            mock_method.is_default = True
            mock_update.return_value = mock_method
            mock_set_default.return_value = mock_method

            res = client.put(
                "/api/v1/payments/methods/11111111-1111-1111-1111-111111111111",
                json={"details": {"label": "My Card"}, "is_default": True},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["is_default"] is True

    @patch("app.api.v1.endpoints.payments.stripe")
    def test_create_transaction(self, mock_stripe):
        mock_intent = Mock()
        mock_intent.id = "pi_txn"
        mock_intent.status = "succeeded"
        mock_intent.amount = 999
        mock_intent.currency = "usd"
        mock_stripe.PaymentIntent.create.return_value = mock_intent

        res = client.post(
            "/api/v1/payments/transactions",
            json={
                "amount": 999,
                "currency": "USD",
                "description": "test txn",
                "payment_method_id": "pm_abc",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == "pi_txn"
        assert data["status"] == "succeeded"


