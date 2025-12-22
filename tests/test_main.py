from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import DBOrder, DBOrderItem, DBAddress
import uuid
import pytest

client = TestClient(app)

# Helper to clean up DB between tests if needed, 
# but for now we rely on unique data or persistent DB if local.
# Ideally, we'd override get_db dependency to use a test DB.
# For this task, we'll write tests that create their own data.

@pytest.fixture(scope="module")
def setup_address():
    """Create a temporary address for testing orders."""
    payload = {
        "recipient": "Test User",
        "phone": "1234567890",
        "address": "123 Test St",
        "city": "Test City",
        "state": "Test State",
        "zip_code": 12345,
        "notes": "Test Note"
    }
    response = client.post("/addresses", json=payload)
    assert response.status_code == 200
    return response.json()["data"]

# --- Address Tests ---

def test_create_address():
    payload = {
        "recipient": "New Recipient",
        "phone": "0987654321",
        "address": "456 New St",
        "city": "New City",
        "state": "New State",
        "zip_code": 54321,
        "notes": "New Note"
    }
    response = client.post("/addresses", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["recipient"] == "New Recipient"
    assert "id" in data["data"]

def test_read_addresses():
    response = client.get("/addresses")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)

def test_read_address(setup_address):
    address_id = setup_address["id"]
    response = client.get(f"/addresses/{address_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == address_id

def test_update_address(setup_address):
    address_id = setup_address["id"]
    payload = setup_address.copy()
    payload["recipient"] = "Updated Recipient"
    
    response = client.put(f"/addresses/{address_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["recipient"] == "Updated Recipient"

def test_delete_address():
    # Create specific address to delete
    payload = {
        "recipient": "Delete Me",
        "phone": "0000000000",
        "address": "Delete St",
        "city": "Delete City",
        "state": "Delete State",
        "zip_code": 00000,
        "notes": "Delete Note"
    }
    create_resp = client.post("/addresses", json=payload)
    address_id = create_resp.json()["data"]["id"]
    
    # Delete it
    response = client.delete(f"/addresses/{address_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify it's gone
    get_resp = client.get(f"/addresses/{address_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["success"] is False # Should fail or return false success if managed that way

# --- Order Tests ---

def test_create_order(setup_address):
    address_id = setup_address["id"]
    payload = {
        "title": "Test Order",
        "product": "Test Product",
        "deadline": "25/12/2025",
        "address_id": address_id,
        "order_items": [
            {"size": 1, "amount": 2}, 
            {"size": 3, "amount": 1}
        ]
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_read_orders_details(setup_address):
    response = client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) > 0
    
    # Check structure of first order
    order = data["data"][0]
    assert "address" in order
    assert "order_items" in order

def test_read_single_order_details(setup_address):
    # Ensure there is an order
    address_id = setup_address["id"]
    unique_title = f"Single Order {uuid.uuid4()}"
    payload = {
        "title": unique_title,
        "product": "Product Single",
        "deadline": "26/12/2025",
        "address_id": address_id,
        "order_items": [{"size": 2, "amount": 1}]
    }
    client.post("/orders", json=payload)
    
    # Find it
    list_resp = client.get("/orders")
    orders = list_resp.json()["data"]
    target_order = None
    for o in orders:
        if o["client"] == unique_title:
             target_order = o
             break
    assert target_order is not None
    
    # Get Detail
    order_id = target_order["id"]
    response = client.get(f"/order/{order_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    detail = data["data"]
    assert detail["id"] == order_id
    assert detail["address"]["id"] == address_id
    assert len(detail["order_items"]) == 1

def test_delete_order_and_items(setup_address):
    address_id = setup_address["id"]
    unique_title = f"To Delete {uuid.uuid4()}"
    payload = {
        "title": unique_title,
        "product": "Product Delete",
        "deadline": "27/12/2025",
        "address_id": address_id,
        "order_items": [{"size": 4, "amount": 5}]
    }
    client.post("/orders", json=payload)
    
    # Find ID
    list_resp = client.get("/orders")
    orders = list_resp.json()["data"]
    order_id = None
    for o in orders:
        if o["client"] == unique_title:
            order_id = o["id"]
            break
    assert order_id is not None
    
    # Delete
    response = client.delete(f"/order/{order_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify Gone (404 or False success)
    get_resp = client.get(f"/order/{order_id}")
    assert get_resp.status_code == 200
    # Expected: "Order not found" with success=False, message set.
    # The models define OrderDetailsResponse data as Optional.
    # If order not found, get_order_details returns {success: False, message: Error(...), data: None}
    assert get_resp.json()["success"] is False
