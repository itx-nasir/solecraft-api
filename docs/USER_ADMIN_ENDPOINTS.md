# SoleCraft API Endpoints by User Role

This document provides a clear separation of API endpoints based on user roles: Normal Users (including guests and authenticated users) and Administrators.

---

## 👤 User Endpoints

These endpoints are accessible to the general public, including guest and authenticated users.

### Health & Utility
- `GET /`: API root endpoint with basic information.
- `GET /health`: Application health check.

### Authentication
- `POST /auth/register`: Register a new user account.
- `POST /auth/login`: Authenticate a user.
- `POST /auth/guest`: Create a guest user session.
- `POST /auth/verify-email`: Verify a user's email address.
- `POST /auth/resend-verification`: Resend the verification email.

### User Profile & Addresses
- `GET /users/profile`: Get the current user's profile.
- `PUT /users/profile`: Update the current user's profile.
- `GET /users/addresses`: Get all of the user's addresses.
- `POST /users/addresses`: Add a new address.
- `PUT /users/addresses/{address_id}`: Update an existing address.
- `DELETE /users/addresses/{address_id}`: Delete an address.

### Products & Categories
- `GET /products`: Get a paginated list of products.
- `GET /products/{product_id}`: Get detailed information for a single product.

### Cart
- `GET /cart`: Get the current user's shopping cart.
- `POST /cart/items`: Add an item to the cart.
- `PUT /cart/items/{item_id}`: Update an item's quantity or customizations in the cart.
- `DELETE /cart/items/{item_id}`: Remove an item from the cart.
- `DELETE /cart`: Clear all items from the cart.

### Orders
- `POST /orders/checkout`: Create an order from the user's cart.
- `GET /orders`: Get the user's order history.
- `GET /orders/{order_id}`: Get detailed information for a specific order.

### Discounts
- `POST /discounts/validate`: Validate a discount code against a cart total.

### Reviews
- `POST /reviews`: Submit a review for a product.
- `GET /reviews/product/{product_id}`: Get all reviews for a specific product.
- `PUT /reviews/{review_id}`: Update a review submitted by the user.
- `DELETE /reviews/{review_id}`: Delete a review submitted by the user.

### Search
- `GET /search/products`: Search for products with optional filters.

---

## 🔒 Admin Endpoints

These endpoints are protected and require administrator privileges.

### Product Management
- `POST /products`: Create a new product.
- `PUT /products/{product_id}`: Update an existing product.
- `DELETE /products/{product_id}`: Delete a product.



### Discount Management
- `POST /discounts`: Create a new discount code.
- `GET /discounts`: Get a list of all discount codes.
- `PUT /discounts/{discount_id}`: Update an existing discount code.
- `DELETE /discounts/{discount_id}`: Delete a discount code.

### Admin Dashboard & Order Management
- `GET /admin/dashboard`: Get dashboard statistics (total users, orders, etc.).
- `GET /admin/orders`: Get a list of all orders in the system.
- `PUT /admin/orders/{order_id}/status`: Update the status of any order. 