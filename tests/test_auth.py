"""
Authentication API tests.
"""

import pytest
from httpx import AsyncClient


class TestAuth:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient, sample_user_data):
        """Test successful user registration."""
        response = await client.post("/auth/register", json=sample_user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "User registered successfully"
        assert "access_token" in data["data"]
        assert data["data"]["user"]["email"] == sample_user_data["email"]
        assert data["data"]["user"]["is_guest"] is False
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, client: AsyncClient, sample_user_data):
        """Test registration with duplicate email."""
        # Register first user
        await client.post("/auth/register", json=sample_user_data)
        
        # Try to register with same email
        response = await client.post("/auth/register", json=sample_user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_user_invalid_email(self, client: AsyncClient, sample_user_data):
        """Test registration with invalid email."""
        sample_user_data["email"] = "invalid-email"
        
        response = await client.post("/auth/register", json=sample_user_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, sample_user_data):
        """Test successful login."""
        # Register user first
        await client.post("/auth/register", json=sample_user_data)
        
        # Login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "Login successful"
        assert "access_token" in data["data"]
        assert data["data"]["user"]["email"] == sample_user_data["email"]
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient, sample_user_data):
        """Test login with invalid credentials."""
        # Register user first
        await client.post("/auth/register", json=sample_user_data)
        
        # Login with wrong password
        login_data = {
            "email": sample_user_data["email"],
            "password": "wrong_password"
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_create_guest_user(self, client: AsyncClient, sample_guest_data):
        """Test guest user creation."""
        response = await client.post("/auth/guest", json=sample_guest_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "Guest user created successfully"
        assert "access_token" in data["data"]
        assert data["data"]["user"]["session_id"] == sample_guest_data["session_id"]
        assert data["data"]["user"]["is_guest"] is True
    
    @pytest.mark.asyncio
    async def test_create_guest_user_existing_session(self, client: AsyncClient, sample_guest_data):
        """Test guest user creation with existing session."""
        # Create first guest user
        await client.post("/auth/guest", json=sample_guest_data)
        
        # Try to create with same session_id
        response = await client.post("/auth/guest", json=sample_guest_data)
        
        assert response.status_code == 201  # Should still work, returning existing user
        data = response.json()
        assert data["success"] is True 