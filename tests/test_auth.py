def test_login_success(client, test_users):
    response = client.post(
        "/auth/login",
        json={
            "email": "employee@test.com",
            "password": "Employee123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, test_users):
    response = client.post(
        "/auth/login",
        json={
            "email": "employee@test.com",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401