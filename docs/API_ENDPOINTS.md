# SoleCraft API Endpoints Documentation

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication
All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Standard Response Format
All API responses follow this standard format:
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {...},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

For paginated responses:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5,
  "has_next": true,
  "has_prev": false
}
```

## Error Response Format
```json
{
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## 🔐 Authentication Endpoints

### POST `/auth/register`
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "phone": "+1234567890"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "is_verified": false
    }
  }
}
```

### POST `/auth/login`
Authenticate user with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123!"
}
```

**Response:** Same as register

### POST `/auth/guest`
Create a guest user session for anonymous checkout.

**Request Body:**
```json
{
  "session_id": "unique-session-id",
  "email": "guest@example.com",
  "first_name": "Guest",
  "last_name": "User"
}
```

**Response:** Same token format as login

### POST `/auth/verify-email`
Verify user email with token.

**Request Body:**
```json
{
  "token": "verification-token"
}
```

### POST `/auth/resend-verification`
Resend verification email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

---

## 👤 User Profile Endpoints

### GET `/users/profile`
Get current user's profile information.
**Auth Required:** Yes

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "is_guest": false,
    "is_active": true,
    "is_verified": true,
    "is_staff": false,
    "last_login": "2024-01-01T00:00:00Z",
    "created_at": "2024-01-01T00:00:00Z",
    "addresses": [],
    "roles": []
  }
}
```

### PUT `/users/profile`
Update user profile information.
**Auth Required:** Yes

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "username": "janesmith",
  "phone": "+1987654321"
}
```

### GET `/users/addresses`
Get all user addresses.
**Auth Required:** Yes

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "label": "Home",
      "first_name": "John",
      "last_name": "Doe",
      "company": "Acme Corp",
      "street_address_1": "123 Main St",
      "street_address_2": "Apt 4B",
      "city": "New York",
      "state": "NY",
      "postal_code": "10001",
      "country": "US",
      "phone": "+1234567890",
      "is_default": true
    }
  ]
}
```

### POST `/users/addresses`
Add a new address.
**Auth Required:** Yes

**Request Body:**
```json
{
  "label": "Work",
  "first_name": "John",
  "last_name": "Doe",
  "company": "Tech Corp",
  "street_address_1": "456 Tech Ave",
  "street_address_2": "Suite 100",
  "city": "San Francisco",
  "state": "CA",
  "postal_code": "94105",
  "country": "US",
  "phone": "+1234567890",
  "is_default": false
}
```

### PUT `/users/addresses/{address_id}`
Update an existing address.
**Auth Required:** Yes

### DELETE `/users/addresses/{address_id}`
Delete an address.
**Auth Required:** Yes

---

## 🛍️ Product Endpoints

### GET `/products`
Get paginated list of products with optional filters.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)
- `is_featured` (bool): Filter featured products

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Classic Sneaker",
      "slug": "classic-sneaker",
      "short_description": "Comfortable everyday sneaker",
      "base_price": 99.99,
      "is_featured": true,
      "images": ["url1", "url2"]
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "has_next": true,
  "has_prev": false
}
```

### GET `/products/{product_id}`
Get detailed product information by ID.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Classic Sneaker",
    "slug": "classic-sneaker",
    "description": "Full product description...",
    "short_description": "Brief description",
    "base_price": 99.99,
    "is_active": true,
    "is_featured": true,
    "is_customizable": true,
    "meta_title": "SEO Title",
    "meta_description": "SEO Description",
    "specifications": {
      "material": "Canvas",
      "sole": "Rubber"
    },
    "images": ["url1", "url2", "url3"]
  }
}
```

### GET `/products/slug/{slug}`
Get product by URL slug.

**Response:** Same as GET by ID

### POST `/products` 🔒
Create a new product.
**Auth Required:** Yes (product:create permission)

**Request Body:**
```json
{
  "name": "New Sneaker",
  "slug": "new-sneaker",
  "base_price": 129.99,
  "description": "Product description",
  "short_description": "Brief description",
  "is_active": true,
  "is_featured": false,
  "is_customizable": true,
  "specifications": {
    "material": "Leather"
  },
  "images": ["url1", "url2"]
}
```

### PUT `/products/{product_id}` 🔒
Update product information.
**Auth Required:** Yes (product:update permission)

### DELETE `/products/{product_id}` 🔒
Delete a product.
**Auth Required:** Yes (product:delete permission)

---

## 🛒 Cart Endpoints

### GET `/cart`
Get current user's cart.
**Auth Required:** Yes

### POST `/cart/items`
Add item to cart.
**Auth Required:** Yes

**Request Body:**
```json
{
  "product_variant_id": "uuid",
  "quantity": 2
}
```

### PUT `/cart/items/{item_id}`
Update cart item quantity.
**Auth Required:** Yes

### DELETE `/cart/items/{item_id}`
Remove item from cart.
**Auth Required:** Yes

### GET `/cart/summary`
Get cart summary with totals.
**Auth Required:** Yes

---

## 📦 Order Endpoints

### POST `/checkout`
Create order from cart.
**Auth Required:** Yes

**Request Body:**
```json
{
  "shipping_address_id": "uuid",
  "billing_address_id": "uuid",
  "shipping_method": "standard",
  "payment_method": "stripe",
  "discount_code": "SAVE10",
  "customer_notes": "Please ring doorbell"
}
```

### GET `/orders`
Get user's order history.
**Auth Required:** Yes

### GET `/orders/{order_id}`
Get detailed order information.
**Auth Required:** Yes

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "order_number": "ORD-001234",
    "status": "confirmed",
    "payment_status": "completed",
    "subtotal": 199.98,
    "tax_amount": 16.00,
    "shipping_amount": 9.99,
    "discount_amount": 20.00,
    "total_amount": 205.97,
    "shipping_address": {...},
    "billing_address": {...},
    "shipping_method": "standard",
    "tracking_number": "1Z999AA1234567890",
    "payment_method": "stripe",
    "confirmed_at": "2024-01-01T10:00:00Z",
    "shipped_at": "2024-01-02T14:30:00Z",
    "delivered_at": null,
    "customer_notes": "Please ring doorbell",
    "items": [
      {
        "id": "uuid",
        "product_name": "Classic Sneaker",
        "variant_name": "Size 8 - White",
        "sku": "CS-8-WHITE",
        "quantity": 2,
        "unit_price": 99.99,
        "total_price": 199.98
      }
    ]
  }
}
```

---

## 📊 Admin Endpoints

### GET `/admin/dashboard`
Get admin dashboard statistics.
**Auth Required:** Yes (admin role)

### GET `/admin/orders`
Get all orders for admin management.
**Auth Required:** Yes (order:read permission)

### PUT `/admin/orders/{order_id}/status`
Update order status.
**Auth Required:** Yes (order:update permission)

---

## 🔍 Search Endpoints

### GET `/search/products`
Search products with filters.

**Query Parameters:**
- `q` (string): Search query
- `min_price` (decimal): Minimum price
- `max_price` (decimal): Maximum price
- `size` (string): Filter by size
- `color` (string): Filter by color
- `sort` (string): Sort by (price_asc, price_desc, name, newest)

---

## 📱 Health & Utility Endpoints

### GET `/health`
Application health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}
```

### GET `/`
API root endpoint with basic information.

---

## 🔐 Permission System

The API uses a role-based access control (RBAC) system with the following roles:

- **customer** (Level 1): Regular users
- **customer_service** (Level 10): Customer support
- **order_fulfillment** (Level 15): Order processing
- **inventory_manager** (Level 20): Product management
- **marketing_manager** (Level 20): Marketing and promotions
- **admin** (Level 90): System administration
- **super_admin** (Level 100): Full access

## 📝 Rate Limiting

- Most endpoints: 60 requests per minute
- Authentication endpoints: 5-20 requests per minute
- Admin endpoints: 10 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

## 🚨 Error Codes

- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Too Many Requests
- `500` - Internal Server Error

## 📋 Test Credentials

### Admin User
- **Email**: `admin@solecraft.com`
- **Password**: `admin123!`
- **Role**: super_admin

### Product Manager
- **Email**: `manager@solecraft.com`
- **Password**: `manager123!`
- **Role**: inventory_manager

## 🔗 Frontend Integration Notes

1. **Authentication**: Store JWT token in secure storage (httpOnly cookie recommended)
2. **Error Handling**: All endpoints return consistent error format
3. **Loading States**: Use response times for loading indicators
4. **Pagination**: Implement infinite scroll or pagination UI
5. **Real-time Updates**: Consider WebSocket for order status updates
6. **Image Optimization**: Product images should be optimized for web
7. **SEO**: Use product slugs for SEO-friendly URLs
8. **Guest Checkout**: Support guest users with session management

## 📋 Notes for Frontend Development

1. **Cart & Order endpoints** are defined in schemas and now implemented in API routes.
2. **Search functionality** is now exposed via API routes.
3. **File upload** for product images is configured but routes not implemented.
4. **Review system** is defined in schemas and now implemented in API routes.
5. **Discount system** is defined in schemas and now implemented in API routes.

## 🚀 Implementation Status

✅ **Completed:**
- Authentication (register, login, guest)
- User profile management
- User address management
- Product CRUD operations
- Product listing with filters
- RBAC permission system
- Rate limiting
- Health checks
- Cart management endpoints
- Order management endpoints
- Search endpoints
- Review endpoints
- Discount/coupon endpoints
- Admin dashboard endpoints

⏳ **To Be Implemented:**
- File upload endpoints
- Granular, role-based permissions (currently uses simple admin checks)
- Payment Gateway Integration (Stripe, etc.)
- Email Notifications (Welcome, Order Confirmation, etc.)
- Advanced Search (e.g., Elasticsearch)
- Wishlist functionality
- Product recommendations 