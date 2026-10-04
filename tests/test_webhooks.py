import pytest


def create_payment(client) -> dict:
    response = client.post(
        "/payments",
        json={
            "tariff_id": 2,
            "email": "webhook@example.com",
            "method": "card",
        },
    )

    assert response.status_code == 201

    return response.json()


@pytest.mark.parametrize(
    "target_status",
    [
        "succeeded",
        "failed",
    ],
)
def test_valid_transition_from_pending(
    client,
    target_status,
):
    payment = create_payment(client)

    response = client.post(
        "/webhooks/bank",
        json={
            "payment_id": payment["id"],
            "status": target_status,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "result": "ok",
    }

    payment_response = client.get(
        f"/payments/{payment['id']}"
    )

    assert payment_response.status_code == 200
    assert (
        payment_response.json()["status"]
        == target_status
    )


def test_valid_transition_from_succeeded_to_refunded(client):
    payment = create_payment(client)

    succeeded_response = client.post(
        "/webhooks/bank",
        json={
            "payment_id": payment["id"],
            "status": "succeeded",
        },
    )

    assert succeeded_response.status_code == 200

    refunded_response = client.post(
        "/webhooks/bank",
        json={
            "payment_id": payment["id"],
            "status": "refunded",
        },
    )

    assert refunded_response.status_code == 200
    assert refunded_response.json() == {
        "result": "ok",
    }

    payment_response = client.get(
        f"/payments/{payment['id']}"
    )

    assert payment_response.json()["status"] == "refunded"


@pytest.mark.parametrize(
    ("first_status", "invalid_status"),
    [
        ("succeeded", "pending"),
        ("failed", "succeeded"),
        ("failed", "refunded"),
        ("refunded", "succeeded"),
    ],
)
def test_invalid_transition_returns_409_and_keeps_status(
    client,
    first_status,
    invalid_status,
):
    payment = create_payment(client)
    payment_id = payment["id"]

    if first_status == "refunded":
        succeeded_response = client.post(
            "/webhooks/bank",
            json={
                "payment_id": payment_id,
                "status": "succeeded",
            },
        )

        assert succeeded_response.status_code == 200

        first_response = client.post(
            "/webhooks/bank",
            json={
                "payment_id": payment_id,
                "status": "refunded",
            },
        )
    else:
        first_response = client.post(
            "/webhooks/bank",
            json={
                "payment_id": payment_id,
                "status": first_status,
            },
        )

    assert first_response.status_code == 200

    invalid_response = client.post(
        "/webhooks/bank",
        json={
            "payment_id": payment_id,
            "status": invalid_status,
        },
    )

    assert invalid_response.status_code == 409
    assert invalid_response.json() == {
        "error": "invalid_transition",
    }

    payment_response = client.get(
        f"/payments/{payment_id}"
    )

    assert payment_response.status_code == 200
    assert (
        payment_response.json()["status"]
        == first_status
    )


def test_same_status_transition_is_forbidden(client):
    payment = create_payment(client)

    response = client.post(
        "/webhooks/bank",
        json={
            "payment_id": payment["id"],
            "status": "pending",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "error": "invalid_transition",
    }

    payment_response = client.get(
        f"/payments/{payment['id']}"
    )

    assert payment_response.json()["status"] == "pending"


def test_webhook_for_unknown_payment_returns_404(client):
    response = client.post(
        "/webhooks/bank",
        json={
            "payment_id": 999999,
            "status": "succeeded",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Payment not found",
    }


def test_webhook_with_unknown_status_returns_422(client):
    payment = create_payment(client)

    response = client.post(
        "/webhooks/bank",
        json={
            "payment_id": payment["id"],
            "status": "unknown",
        },
    )

    assert response.status_code == 422