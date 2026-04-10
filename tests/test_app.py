import pytest
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import app, init_db


@pytest.fixture
def client(tmp_path):
    db_file = str(tmp_path / "test.db")
    app.config["TESTING"] = True
    os.environ["DB_PATH"] = db_file
    # reload DB_PATH inside app module
    import app as app_module
    app_module.DB_PATH = db_file
    init_db()
    with app.test_client() as client:
        yield client


def create_account(client, account_id="ACC001", name="Test User"):
    return client.post("/account", json={"account_id": account_id, "name": name})


def test_create_account(client):
    res = create_account(client)
    assert res.status_code == 201
    data = json.loads(res.data)
    assert data["account_id"] == "ACC001"


def test_create_duplicate_account(client):
    create_account(client)
    res = create_account(client)
    assert res.status_code == 409


def test_deposit(client):
    create_account(client)
    res = client.post("/deposit", json={"account_id": "ACC001", "amount": 1000})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["new_balance"] == 1000


def test_withdraw(client):
    create_account(client)
    client.post("/deposit", json={"account_id": "ACC001", "amount": 5000})
    res = client.post("/withdraw", json={"account_id": "ACC001", "amount": 2000})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["new_balance"] == 3000


def test_withdraw_insufficient_funds(client):
    create_account(client)
    client.post("/deposit", json={"account_id": "ACC001", "amount": 500})
    res = client.post("/withdraw", json={"account_id": "ACC001", "amount": 1000})
    assert res.status_code == 400
    data = json.loads(res.data)
    assert "Insufficient" in data["error"]


def test_get_balance(client):
    create_account(client)
    client.post("/deposit", json={"account_id": "ACC001", "amount": 2500})
    res = client.get("/balance/ACC001")
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data["balance"] == 2500


def test_fraud_flag_on_deposit(client):
    create_account(client)
    res = client.post("/deposit", json={"account_id": "ACC001", "amount": 75000})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert "warning" in data
    assert "fraud" in data["warning"].lower()


def test_fraud_flag_on_withdrawal(client):
    create_account(client)
    client.post("/deposit", json={"account_id": "ACC001", "amount": 200000})
    res = client.post("/withdraw", json={"account_id": "ACC001", "amount": 60000})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert "warning" in data


def test_account_not_found(client):
    res = client.get("/balance/NONEXISTENT")
    assert res.status_code == 404


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
