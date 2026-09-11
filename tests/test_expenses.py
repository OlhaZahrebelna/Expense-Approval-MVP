def login(client, email, password):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def test_employee_can_create_expense(client, test_users):
    headers = login(
        client,
        "employee@test.com",
        "Employee123",
    )

    response = client.post(
        "/expenses",
        headers=headers,
        json={
            "amount": 120.50,
            "category_id": test_users["travel"].id,
            "description": "Flight ticket to Berlin",
            "expense_date": "2026-09-10",
            "payment_details": "Bank transfer",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "pending"
    assert data["employee_id"] == test_users["employee"].id
    assert data["approver_id"] == test_users["travel_approver"].id


def test_approver_sees_assigned_queue(client, test_users):
    employee_headers = login(
        client,
        "employee@test.com",
        "Employee123",
    )

    client.post(
        "/expenses",
        headers=employee_headers,
        json={
            "amount": 250,
            "category_id": test_users["travel"].id,
            "description": "Hotel in London",
            "expense_date": "2026-09-10",
            "payment_details": "Bank transfer",
        },
    )

    approver_headers = login(
        client,
        "travel@test.com",
        "Travel123",
    )

    response = client.get(
        "/expenses/queue",
        headers=approver_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["description"] == "Hotel in London"
    assert data[0]["status"] == "pending"


def test_approver_can_approve_expense(client, test_users):
    employee_headers = login(
        client,
        "employee@test.com",
        "Employee123",
    )

    create_response = client.post(
        "/expenses",
        headers=employee_headers,
        json={
            "amount": 300,
            "category_id": test_users["travel"].id,
            "description": "Flight to Paris",
            "expense_date": "2026-09-10",
            "payment_details": "Bank transfer",
        },
    )

    expense_id = create_response.json()["id"]

    approver_headers = login(
        client,
        "travel@test.com",
        "Travel123",
    )

    response = client.post(
        f"/expenses/{expense_id}/approve",
        headers=approver_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_approver_can_reject_with_comment(client, test_users):
    employee_headers = login(
        client,
        "employee@test.com",
        "Employee123",
    )

    create_response = client.post(
        "/expenses",
        headers=employee_headers,
        json={
            "amount": 150,
            "category_id": test_users["office"].id,
            "description": "Office chair",
            "expense_date": "2026-09-10",
            "payment_details": "Bank transfer",
        },
    )

    expense_id = create_response.json()["id"]

    approver_headers = login(
        client,
        "finance@test.com",
        "Finance123",
    )

    response = client.post(
        f"/expenses/{expense_id}/reject",
        headers=approver_headers,
        json={
            "comment": "Receipt is missing."
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "rejected"
    assert data["rejection_comment"] == "Receipt is missing."


def test_reject_without_comment_fails(client, test_users):
    employee_headers = login(
        client,
        "employee@test.com",
        "Employee123",
    )

    create_response = client.post(
        "/expenses",
        headers=employee_headers,
        json={
            "amount": 150,
            "category_id": test_users["office"].id,
            "description": "Office chair",
            "expense_date": "2026-09-10",
            "payment_details": "Bank transfer",
        },
    )

    expense_id = create_response.json()["id"]

    approver_headers = login(
        client,
        "finance@test.com",
        "Finance123",
    )

    response = client.post(
        f"/expenses/{expense_id}/reject",
        headers=approver_headers,
        json={
            "comment": ""
        },
    )

    assert response.status_code == 422


def test_wrong_approver_cannot_approve(client, test_users):
    employee_headers = login(
        client,
        "employee@test.com",
        "Employee123",
    )

    create_response = client.post(
        "/expenses",
        headers=employee_headers,
        json={
            "amount": 400,
            "category_id": test_users["travel"].id,
            "description": "Flight to Rome",
            "expense_date": "2026-09-10",
            "payment_details": "Bank transfer",
        },
    )

    expense_id = create_response.json()["id"]

    wrong_approver_headers = login(
        client,
        "finance@test.com",
        "Finance123",
    )

    response = client.post(
        f"/expenses/{expense_id}/approve",
        headers=wrong_approver_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You are not assigned to this expense"


def test_employee_can_withdraw_pending_expense(client, test_users):
    employee_headers = login(
        client,
        "employee@test.com",
        "Employee123",
    )

    create_response = client.post(
        "/expenses",
        headers=employee_headers,
        json={
            "amount": 80,
            "category_id": test_users["office"].id,
            "description": "Office supplies",
            "expense_date": "2026-09-10",
            "payment_details": "Bank transfer",
        },
    )

    expense_id = create_response.json()["id"]

    response = client.post(
        f"/expenses/{expense_id}/withdraw",
        headers=employee_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "withdrawn"


def test_ai_failure_does_not_block_expense(
    client,
    test_users,
    monkeypatch,
):
    employee_headers = login(
        client,
        "employee@test.com",
        "Employee123",
    )

    create_response = client.post(
        "/expenses",
        headers=employee_headers,
        json={
            "amount": 500,
            "category_id": test_users["travel"].id,
            "description": "Flight to Madrid",
            "expense_date": "2026-09-10",
            "payment_details": "Bank transfer",
        },
    )

    expense_id = create_response.json()["id"]

    approver_headers = login(
        client,
        "travel@test.com",
        "Travel123",
    )

    def fake_ai_failure(*args, **kwargs):
        raise RuntimeError("AI service unavailable")

    monkeypatch.setattr(
        "app.expenses.analyze_expense",
        fake_ai_failure,
    )

    response = client.get(
        f"/expenses/{expense_id}",
        headers=approver_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == expense_id
    assert data["ai_analysis"] is None    