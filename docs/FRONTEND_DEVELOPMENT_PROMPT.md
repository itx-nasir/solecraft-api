# SoleCraft Frontend Development Prompt

I am building a frontend application for a **custom shoe-selling platform** using **Next.js (with TypeScript)** and **Tailwind CSS**.

## 🎯 Project Requirements

### Tech Stack
- **Framework**: Next.js 14+ with TypeScript
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand for cart and user session
- **API Communication**: React Query (TanStack Query) or Axios
- **Form Handling**: React Hook Form with validation
- **Animations**: Framer Motion (bonus)

### Project Structure
Follow modular folder structure with atomic component design and Clean Code principles:

```
src/
├── components/
│   ├── ui/           # Reusable UI blocks (shadcn/ui)
│   ├── pages/        # Page-level composition
│   └── common/       # Common components (header, footer, etc.)
├── lib/              # Helper utilities
├── hooks/            # Custom hooks for API, cart management, etc.
├── stores/           # Zustand stores
├── types/            # TypeScript type definitions
├── utils/            # Utility functions
└── app/              # Next.js 14 app directory
```

## 🛍️ Required Routes & Features

### Public Routes
1. **Home page** (`/`) - Showcase featured shoes, hero section, categories
2. **Product listing** (`/products`) - Grid/list view with filters and pagination
3. **Product details** (`/products/[slug]`) - Detailed product view with customization options
4. **Cart** (`/cart`) - Shopping cart with item management
5. **Checkout** (`/checkout`) - Multi-step checkout process
6. **Order summary** (`/order/[id]`) - Order confirmation and details
7. **Login/Signup** (`/auth/login`, `/auth/register`) - Authentication pages

### Protected Routes
8. **User Dashboard** (`/account`) - Profile, orders, addresses
9. **Order History** (`/account/orders`) - List of user orders
10. **Admin Dashboard** (`/admin`) - Basic scaffolding for admin features

## 🔌 Backend API Integration

### API Base URL
- **Development**: `http://localhost:8000`
- **Production**: Configure via environment variables

### Authentication
- **JWT Token Storage**: Use secure httpOnly cookies or localStorage
- **Token Format**: `Bearer <jwt_token>` in Authorization header
- **Guest Support**: Full guest checkout without registration required

### Available Endpoints (✅ Implemented)

#### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login  
- `POST /auth/guest` - Create guest session
- `POST /auth/verify-email` - Email verification
- `POST /auth/resend-verification` - Resend verification

#### User Management
- `GET /users/profile` - Get user profile
- `PUT /users/profile` - Update profile
- `GET /users/addresses` - Get user addresses
- `POST /users/addresses` - Add new address
- `PUT /users/addresses/{id}` - Update address
- `DELETE /users/addresses/{id}` - Delete address

#### Products
- `GET /products` - List products (with pagination, category filter, featured filter)
- `GET /products/{id}` - Get product by ID
- `GET /products/slug/{slug}` - Get product by slug
- `POST /products` - Create product (admin only)
- `PUT /products/{id}` - Update product (admin only)
- `DELETE /products/{id}` - Delete product (admin only)

#### Utility
- `GET /health` - Health check
- `GET /` - API info

### Mock/Placeholder Endpoints (⏳ To Be Implemented)
*Create mock data or placeholder functions for these until backend implements them:*

#### Cart Management
- `GET /cart` - Get user cart
- `POST /cart/items` - Add item to cart
- `PUT /cart/items/{id}` - Update cart item
- `DELETE /cart/items/{id}` - Remove cart item
- `GET /cart/summary` - Get cart totals

#### Orders
- `POST /checkout` - Create order from cart
- `GET /orders` - Get user orders
- `GET /orders/{id}` - Get order details

#### Search & Filters
- `GET /search/products` - Search products with filters

### API Response Format
All responses follow this standard format:
```typescript
interface StandardResponse<T> {
  success: boolean;
  message: string;
  data: T;
  timestamp: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}
```

### Test Credentials
- **Admin**: `admin@solecraft.com` / `admin123!`
- **Product Manager**: `manager@solecraft.com` / `manager123!`

## 🎨 Design Requirements

### UI/UX Standards
- **Clean, modern e-commerce design** with professional aesthetics
- **Mobile-first responsive** design (desktop, tablet, mobile)
- **Consistent component library** using shadcn/ui
- **Loading states** and **error handling** for all API calls
- **Form validations** with clear error messages
- **Accessibility** compliance (ARIA labels, keyboard navigation)

### Key Features to Implement

#### Shopping Experience
- **Product cards** with hover effects and quick actions
- **Advanced filtering** (price range, size, color, category)
- **Product image gallery** with zoom functionality
- **Customization options** (text, colors, materials)
- **Size guide** and product specifications
- **Related products** suggestions

#### Cart & Checkout
- **Persistent cart** (guest and authenticated users)
- **Real-time cart updates** with quantity changes
- **Guest checkout** flow without registration
- **Multi-step checkout** (shipping, payment, review)
- **Address management** with saved addresses
- **Order confirmation** with email notifications

#### User Account
- **Dashboard** with order history and profile
- **Address book** management
- **Order tracking** with status updates
- **Wishlist** functionality (bonus)

#### Admin Features (Basic Scaffolding)
- **Product management** interface
- **Order management** dashboard
- **User management** tools
- **Analytics** overview (placeholder)

## 🛠️ Technical Implementation

### State Management (Zustand)
Create stores for:
```typescript
// Cart Store
interface CartStore {
  items: CartItem[];
  addItem: (item: CartItem) => void;
  removeItem: (id: string) => void;
  updateQuantity: (id: string, quantity: number) => void;
  clearCart: () => void;
  getTotal: () => number;
}

// Auth Store  
interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials: LoginData) => Promise<void>;
  logout: () => void;
  register: (userData: RegisterData) => Promise<void>;
}

// UI Store
interface UIStore {
  isLoading: boolean;
  error: string | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}
```

### Custom Hooks
```typescript
// API Hooks
useProducts(filters?: ProductFilters)
useProduct(slug: string)
useCart()
useOrders()
useAuth()

// UI Hooks
useDebounce(value: string, delay: number)
useLocalStorage(key: string, defaultValue: any)
usePagination(totalItems: number, itemsPerPage: number)
```

### TypeScript Types
```typescript
interface Product {
  id: string;
  name: string;
  slug: string;
  description: string;
  base_price: number;
  images: string[];
  category: Category;
  variants: ProductVariant[];
  is_featured: boolean;
  is_active: boolean;
}

interface CartItem {
  id: string;
  product_variant_id: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  product_variant: ProductVariant;
}

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_guest: boolean;
  addresses: Address[];
}
```

## 📱 Responsive Design

### Breakpoints (Tailwind)
- **Mobile**: `< 640px`
- **Tablet**: `640px - 1024px`  
- **Desktop**: `> 1024px`

### Layout Components
- **Header**: Logo, navigation, search, cart icon, user menu
- **Footer**: Links, newsletter signup, social media
- **Sidebar**: Filters for product listing
- **Product Grid**: Responsive grid (1-2-3-4 columns)

## 🔍 SEO & Performance

### SEO Requirements
- **Dynamic meta tags** for products and categories
- **Structured data** for products (JSON-LD)
- **SEO-friendly URLs** using product slugs
- **Sitemap** generation
- **Open Graph** tags for social sharing

### Performance
- **Image optimization** with Next.js Image component
- **Lazy loading** for product images and components
- **Code splitting** by routes
- **Caching** strategies for API calls
- **Bundle optimization**

## 🚀 Development Priorities

### Phase 1 (Core Features)
1. Set up project structure and basic routing
2. Implement authentication (login, register, guest)
3. Create product listing and detail pages
4. Build shopping cart functionality
5. Implement basic checkout flow

### Phase 2 (Enhanced Features)
1. Add user dashboard and profile management
2. Implement address management
3. Create order history and tracking
4. Add product search and filtering
5. Implement admin dashboard scaffolding

### Phase 3 (Polish & Optimization)
1. Add animations and micro-interactions
2. Implement advanced filtering
3. Add wishlist functionality
4. Optimize performance and SEO
5. Add comprehensive error handling

## 📋 Deliverables

### Required Files
- Complete Next.js application with all routes
- TypeScript type definitions
- Zustand store implementations
- Custom hooks for API integration
- Responsive component library
- Form validation schemas
- Error handling utilities
- README with setup instructions

### Documentation
- Component documentation
- API integration guide
- Deployment instructions
- Environment variable configuration

## 🔗 Additional Resources

- **API Documentation**: See `docs/API_ENDPOINTS.md` for complete endpoint details
- **Design System**: Use shadcn/ui for consistent components
- **Backend Repository**: SoleCraft API (FastAPI + PostgreSQL)
- **Test Data**: Use provided test credentials for development

## ⚠️ Important Notes

1. **Backend API is fully functional** for authentication, users, and products
2. **Cart and order endpoints** need to be mocked until backend implementation
3. **Guest checkout** should work with session-based cart management
4. **Admin features** only need basic scaffolding for now
5. **Error handling** should be comprehensive with user-friendly messages
6. **Loading states** should be implemented for all async operations
7. **Form validation** should match backend validation requirements

This project should result in a **production-ready e-commerce frontend** that integrates seamlessly with the existing SoleCraft API backend.