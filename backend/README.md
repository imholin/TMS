# TMS - Transportation Management System

A Flask-based backend API for express delivery transportation management.

## Features

- **User Authentication**: JWT-based auth with role-based access control
- **Order Management**: Create, confirm, cancel, and track orders
- **Shipment Management**: Assign orders to vehicles/drivers, track shipments
- **Vehicle Management**: Track vehicle status, maintenance, and utilization
- **Driver Management**: Manage driver profiles, status, and assignments
- **Route Management**: Define routes with waypoints, optimization support
- **Expense Tracking**: Record and categorize expenses by vehicle/driver/shipment
- **Dashboard**: Key metrics, revenue trends, and utilization statistics

## Project Structure

```
TMS/backend/
├── app.py              # Flask application factory
├── run.py              # Entry point
├── config.py           # Configuration settings
├── extensions.py       # Flask extensions (db, migrate, jwt)
├── models.py           # Database models
├── requirements.txt    # Python dependencies
└── api/
    ├── __init__.py     # Blueprint registration
    ├── auth.py         # Authentication endpoints
    ├── orders.py       # Order CRUD + workflow
    ├── shipments.py    # Shipment management
    ├── vehicles.py     # Vehicle management
    ├── drivers.py      # Driver management
    ├── routes_api.py   # Route management
    ├── expenses.py     # Expense management
    ├── dashboard.py    # Statistics & reports
    └── utils.py        # Helper functions
```

## Installation

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables (optional):
   ```bash
   export FLASK_ENV=development
   export SECRET_KEY=your-secret-key
   export JWT_SECRET_KEY=your-jwt-secret
   ```

4. Run the application:
   ```bash
   python run.py
   ```

## Default Admin Account

- Username: `admin`
- Password: `admin123`
- Email: `admin@tms.local`

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Register new user (admin only)
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Current user info
- `PUT /api/v1/auth/password` - Change password
- `GET /api/v1/auth/users` - List users (admin only)

### Orders
- `GET /api/v1/orders` - List orders with filters
- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders/<id>` - Get order details
- `PUT /api/v1/orders/<id>` - Update order
- `POST /api/v1/orders/<id>/confirm` - Confirm order
- `POST /api/v1/orders/<id>/cancel` - Cancel order
- `GET /api/v1/orders/<id>/tracking` - Get tracking history

### Shipments
- `GET /api/v1/shipments` - List shipments
- `POST /api/v1/shipments` - Create shipment
- `GET /api/v1/shipments/<id>` - Get shipment details
- `PUT /api/v1/shipments/<id>` - Update shipment
- `POST /api/v1/shipments/<id>/start` - Start shipment
- `POST /api/v1/shipments/<id>/complete` - Complete shipment
- `POST /api/v1/shipments/<id>/tracking` - Add tracking event
- `GET /api/v1/shipments/<id>/tracking` - Get tracking history

### Vehicles
- `GET /api/v1/vehicles` - List vehicles
- `POST /api/v1/vehicles` - Create vehicle (admin)
- `GET /api/v1/vehicles/<id>` - Get vehicle details
- `PUT /api/v1/vehicles/<id>` - Update vehicle
- `DELETE /api/v1/vehicles/<id>` - Retire vehicle (admin)
- `PUT /api/v1/vehicles/<id>/status` - Update status

### Drivers
- `GET /api/v1/drivers` - List drivers
- `POST /api/v1/drivers` - Create driver (admin)
- `GET /api/v1/drivers/<id>` - Get driver details
- `PUT /api/v1/drivers/<id>` - Update driver
- `PUT /api/v1/drivers/<id>/status` - Update status

### Routes
- `GET /api/v1/routes` - List routes
- `POST /api/v1/routes` - Create route
- `GET /api/v1/routes/<id>` - Get route details
- `PUT /api/v1/routes/<id>` - Update route
- `POST /api/v1/routes/<id>/optimize` - Optimize route
- `POST /api/v1/routes/<id>/assign` - Assign to shipment

### Expenses
- `GET /api/v1/expenses` - List expenses
- `POST /api/v1/expenses` - Record expense
- `GET /api/v1/expenses/<id>` - Get expense details
- `PUT /api/v1/expenses/<id>` - Update expense
- `DELETE /api/v1/expenses/<id>` - Delete expense (admin)
- `GET /api/v1/expenses/summary/daily` - Daily summary
- `GET /api/v1/expenses/summary/monthly` - Monthly report

### Dashboard
- `GET /api/v1/dashboard/stats` - Key metrics
- `GET /api/v1/dashboard/orders-by-status` - Order status counts
- `GET /api/v1/dashboard/revenue-trend` - Revenue trend
- `GET /api/v1/dashboard/top-routes` - Top routes
- `GET /api/v1/dashboard/vehicle-utilization` - Vehicle stats

## User Roles

- `admin` - Full access
- `manager` - Manage operations
- `dispatcher` - Create orders, shipments
- `driver` - View assigned shipments
- `viewer` - Read-only access

## Database

Default: SQLite (`tms.db`)

To use PostgreSQL or MySQL, set `DATABASE_URL` environment variable.

## License

MIT
