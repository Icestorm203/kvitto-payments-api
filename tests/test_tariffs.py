def test_get_tariffs(client):
    response = client.get("/tariffs")

    assert response.status_code == 200

    tariffs = response.json()

    assert len(tariffs) == 3

    assert tariffs == [
        {
            "id": 1,
            "title": "basic",
            "price": 990000,
        },
        {
            "id": 2,
            "title": "standard",
            "price": 1990000,
        },
        {
            "id": 3,
            "title": "premium",
            "price": 2990000,
        },
    ]