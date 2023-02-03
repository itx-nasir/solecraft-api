"""
Product API tests.
"""

import pytest
from httpx import AsyncClient


class TestProducts:
    """Test product endpoints."""

    @pytest.mark.asyncio
    async def test_create_product_success(self, client: AsyncClient, admin_user_token: str, sample_product_data: dict):
        """Test successful product creation by an admin."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        response = await client.post("/products", headers=headers, json=sample_product_data)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Product created successfully"
        assert data["data"]["name"] == sample_product_data["name"]
        assert data["data"]["slug"] == sample_product_data["slug"]

    @pytest.mark.asyncio
    async def test_create_product_no_auth(self, client: AsyncClient, sample_product_data: dict):
        """Test product creation without authentication."""
        response = await client.post("/products", json=sample_product_data)
        assert response.status_code == 401  # or 403 if auto_error=False is not used

    @pytest.mark.asyncio
    async def test_create_product_not_admin(self, client: AsyncClient, sample_user_data: dict, sample_product_data: dict):
        """Test product creation by a non-admin user."""
        # Register and log in a regular user
        await client.post("/auth/register", json=sample_user_data)
        login_resp = await client.post("/auth/login", json={"email": sample_user_data["email"], "password": sample_user_data["password"]})
        token = login_resp.json()["data"]["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.post("/products", headers=headers, json=sample_product_data)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_products(self, client: AsyncClient, sample_product_data: dict, admin_user_token: str):
        """Test listing products."""
        # Create a product first
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        await client.post("/products", headers=headers, json=sample_product_data)

        response = await client.get("/products")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == sample_product_data["name"]

    @pytest.mark.asyncio
    async def test_get_product_by_id(self, client: AsyncClient, sample_product_data: dict, admin_user_token: str):
        """Test getting a product by ID."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        create_response = await client.post("/products", headers=headers, json=sample_product_data)
        product_id = create_response.json()["data"]["id"]

        response = await client.get(f"/products/{product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == product_id
        assert data["data"]["name"] == sample_product_data["name"]
    
    @pytest.mark.asyncio
    async def test_get_product_by_slug(self, client: AsyncClient, sample_product_data: dict, admin_user_token: str):
        """Test getting a product by slug."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        await client.post("/products", headers=headers, json=sample_product_data)
        product_slug = sample_product_data["slug"]

        response = await client.get(f"/products/slug/{product_slug}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["slug"] == product_slug

    @pytest.mark.asyncio
    async def test_update_product(self, client: AsyncClient, sample_product_data: dict, admin_user_token: str):
        """Test updating a product."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        create_response = await client.post("/products", headers=headers, json=sample_product_data)
        product_id = create_response.json()["data"]["id"]

        update_data = {"name": "Updated Test Shoe", "base_price": "129.99"}
        response = await client.put(f"/products/{product_id}", headers=headers, json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Test Shoe"
        assert data["data"]["base_price"] == 129.99 # Pydantic converts to float/Decimal

    @pytest.mark.asyncio
    async def test_delete_product(self, client: AsyncClient, sample_product_data: dict, admin_user_token: str):
        """Test deleting a product."""
        headers = {"Authorization": f"Bearer {admin_user_token}"}
        create_response = await client.post("/products", headers=headers, json=sample_product_data)
        product_id = create_response.json()["data"]["id"]

        delete_response = await client.delete(f"/products/{product_id}", headers=headers)
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["success"] is True
        assert data["data"] is True

        # Verify it's gone
        get_response = await client.get(f"/products/{product_id}")
        assert get_response.status_code == 404 