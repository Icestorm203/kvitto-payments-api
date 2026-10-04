import pytest


def test_create_payment_without_promo_code(client):
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "user@example.com",
            "method": "card",
        },
    )

    assert response.status_code == 201

    payment = response.json()

    assert payment["status"] == "pending"
    assert payment["tariff_id"] == 2
    assert payment["amount"] == 1990000
    assert payment["discount"] == 0
    assert payment["method"] == "card"
    assert payment["installment_months"] is None
    assert payment["schedule"] is None
    assert payment["email"] == "user@example.com"
    assert payment["id"] is not None
    assert payment["created_at"] is not None


@pytest.mark.parametrize(
    ("promo_code", "expected_amount", "expected_discount"),
    [
        ("KVITTO10", 1791000, 199000),
        ("kvitto10", 1791000, 199000),
        ("KvItTo10", 1791000, 199000),
    ],
)
def test_create_payment_with_case_insensitive_promo_code(
    client,
    promo_code,
    expected_amount,
    expected_discount,
):
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "promo@example.com",
            "method": "card",
            "promo_code": promo_code,
        },
    )

    assert response.status_code == 201

    payment = response.json()

    assert payment["amount"] == expected_amount
    assert payment["discount"] == expected_discount


def test_unknown_promo_code_returns_422(client):
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "promo@example.com",
            "method": "card",
            "promo_code": "UNKNOWN",
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "months",
    [
        3,
        6,
        12,
    ],
)
def test_installment_schedule_preserves_total_amount(
    client,
    months,
):
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "installment@example.com",
            "method": "installment",
            "installment_months": months,
        },
    )

    assert response.status_code == 201

    payment = response.json()
    schedule = payment["schedule"]

    assert payment["amount"] == 1990000
    assert payment["installment_months"] == months
    assert len(schedule) == months
    assert sum(schedule) == payment["amount"]

    # Размеры соседних платежей отличаются
    # максимум на одну копейку.
    assert max(schedule) - min(schedule) <= 1


def test_three_month_installment_has_expected_schedule(client):
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "schedule@example.com",
            "method": "installment",
            "installment_months": 3,
        },
    )

    assert response.status_code == 201

    payment = response.json()

    assert payment["schedule"] == [
        663334,
        663333,
        663333,
    ]


def test_extra_kopecks_are_added_to_first_payments(client):
    response = client.post(
        "/payments",
        json={
            "tariff_id": 1,
            "email": "remainder@example.com",
            "method": "installment",
            "installment_months": 12,
        },
    )

    assert response.status_code == 201

    payment = response.json()
    schedule = payment["schedule"]

    assert sum(schedule) == 990000

    base_payment = 990000 // 12
    remainder = 990000 % 12

    expected_schedule = [
        base_payment + 1
        if index < remainder
        else base_payment
        for index in range(12)
    ]

    assert schedule == expected_schedule


def test_installment_requires_months(client):
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "installment@example.com",
            "method": "installment",
        },
    )

    assert response.status_code == 422


def test_installment_months_for_card_returns_422(client):
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "card@example.com",
            "method": "card",
            "installment_months": 3,
        },
    )

    assert response.status_code == 422


def test_invalid_payment_method_returns_422(client):
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "method@example.com",
            "method": "cash",
        },
    )

    assert response.status_code == 422


def test_invalid_email_returns_422(client):
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "not-an-email",
            "method": "card",
        },
    )

    assert response.status_code == 422


def test_tariff_not_found(client):
    response = client.post(
        "/payments",
        json={
            "tariff_id": 999,
            "email": "user@example.com",
            "method": "card",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Tariff not found",
    }


def test_idempotency_key_does_not_create_second_payment(
    client,
    db_session,
):
    headers = {
        "Idempotency-Key": "test-order-001",
    }

    payload = {
        "tariff_id": 2,
        "email": "idempotency@example.com",
        "method": "card",
    }

    first_response = client.post(
        "/payments",
        json=payload,
        headers=headers,
    )

    second_response = client.post(
        "/payments",
        json=payload,
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 200

    first_payment = first_response.json()
    second_payment = second_response.json()

    assert first_payment["id"] == second_payment["id"]
    assert first_payment == second_payment

    from app.models import Payment

    payments_count = (
        db_session.query(Payment)
        .filter(
            Payment.idempotency_key == "test-order-001"
        )
        .count()
    )

    assert payments_count == 1


def test_requests_without_idempotency_key_create_two_payments(
    client,
):
    payload = {
        "tariff_id": 1,
        "email": "without-key@example.com",
        "method": "sbp",
    }

    first_response = client.post(
        "/payments",
        json=payload,
    )

    second_response = client.post(
        "/payments",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    assert (
        first_response.json()["id"]
        != second_response.json()["id"]
    )


def test_get_existing_payment(client):
    create_response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "get@example.com",
            "method": "card",
        },
    )

    payment_id = create_response.json()["id"]

    response = client.get(
        f"/payments/{payment_id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == payment_id
    assert response.json()["email"] == "get@example.com"


def test_get_unknown_payment_returns_404(client):
    response = client.get(
        "/payments/999999"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Payment not found",
    }