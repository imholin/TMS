# TMS - Express Delivery Transportation Management System
# TMS - 快递物流运输管理系统

> A full-featured REST API + CLI platform for managing express delivery operations,
> including order lifecycle, vehicle/driver dispatch, route planning, and billing.
> 全功能 REST API + 命令行平台，管理快递配送全流程：订单、车辆、司机、路由、计费。

---

## Table of Contents | 目录

- [Architecture Overview | 系统架构](#architecture-overview--系统架构)
- [Project Structure | 项目结构](#project-structure--项目结构)
- [Quick Start | 快速开始](#quick-start--快速开始)
- [API Reference | API 参考](#api-reference--api-参考)
- [CLI Commands | CLI 命令](#cli-commands--cli-命令)
- [Database Schema | 数据库模型](#database-schema--数据库模型)
- [Authentication | 认证](#authentication--认证)
- [Testing | 测试](#testing--测试)
- [Configuration | 配置](#configuration--配置)

---

## Architecture Overview | 系统架构

```
TMS/
+-- backend/
|   +-- api/          REST API (Flask blueprints)
|   +-- models/       SQLAlchemy ORM models
|   +-- services/     Business logic layer
|   +-- cli.py        Click CLI tool
|   +-- app.py        Flask application factory
|   +-- extensions.py Flask extensions (db, jwt)
|   +-- config.py     Environment configurations
+-- tests/            pytest test suite
+-- instance/         SQLite database (dev)
```

### Tech Stack | 技术栈

| Layer | Technology | 技术 |
|-------|-----------|------|
| Web Framework | Flask 3.0 | Web 框架 |
| ORM | SQLAlchemy 2.0 + Flask-SQLAlchemy | ORM |
| Authentication | Flask-JWT-Extended | JWT 认证 |
| CLI | Click | 命令行工具 |
| Database | SQLite (dev) / PostgreSQL (prod) | 数据库 |
| Testing | pytest + Flask test client | 测试 |

---

## Project Structure | 项目结构

```
TMS/
├── backend/
│   ├── __init__.py
│   ├── app.py                 # Flask application factory
│   ├── config.py              # Environment configurations
│   ├── extensions.py          # Flask extensions (db, jwt, migrate)
│   ├── cli.py                 # Click CLI entry point
│   ├── requirements.txt        # Python dependencies
│   ├── run.py                 # Development server runner
│   │
│   ├── api/                   # REST API blueprints
│   │   ├── __init__.py        # api_bp blueprint registration
│   │   ├── auth.py            # Login, register, token management
│   │   ├── orders.py          # Order CRUD + confirm/cancel
│   │   ├── shipments.py       # Shipment lifecycle
│   │   ├── vehicles.py        # Vehicle management
│   │   ├── drivers.py         # Driver management
│   │   ├── routes_api.py      # Route CRUD + optimization
│   │   ├── expenses.py        # Expense recording + reporting
│   │   └── dashboard.py       # KPI dashboard endpoints
│   │
│   ├── models/                # SQLAlchemy ORM models (package)
│   │   ├── __init__.py        # Package exports
│   │   ├── base.py            # BaseModel (UUID, timestamps)
│   │   ├── user.py            # User model
│   │   ├── order.py           # Order model
│   │   ├── vehicle.py         # Vehicle model
│   │   ├── driver.py          # Driver model
│   │   ├── shipment.py        # Shipment + ShipmentOrder models
│   │   ├── route.py           # Route model
│   │   ├── expense.py          # Expense model
│   │   └── tracking.py         # Tracking + TrackingEvent + ShipmentException
│   │
│   ├── services/              # Business logic services
│   │   ├── order_service.py   # Order lifecycle, fee calculation
│   │   ├── route_service.py   # Distance, waypoint optimization
│   │   ├── billing_service.py # Expense management, reporting
│   │   ├── shipment_service.py
│   │   └── tracking_service.py
│   │
│   └── utils/
│       └── helpers.py
│
├── tests/                     # pytest test suite
│   ├── conftest.py            # Shared fixtures
│   ├── test_models.py         # Model unit tests
│   ├── test_services.py       # Service unit tests
│   └── test_api.py            # API endpoint tests
│
└── README.md
```

---

## Quick Start | 快速开始

### Prerequisites | 前置条件

- Python 3.9+
- pip

### Installation | 安装

```bash
cd TMS
pip install -r backend/requirements.txt
```

### Initialize Database | 初始化数据库

```bash
python backend/cli.py db init
```

### Seed Demo Data | 种子数据

```bash
python backend/cli.py db seed
```

Creates:
- 8 vehicles (vans/trucks in major cities)
- 8 drivers with B-class licenses
- 20 sample orders across various cities and statuses
- Default admin: `admin` / `admin123`

### Run Development Server | 启动开发服务器

```bash
python backend/run.py
# or
cd backend && flask run --host=0.0.0.0 --port=5000
```

---

## CLI Commands | CLI 命令

```bash
# === Database ===
python backend/cli.py db init              # Create all tables
python backend/cli.py db seed              # Seed demo data
python backend/cli.py db reset             # Drop + recreate tables

# === Orders ===
python backend/cli.py order <ORDER_NO>              # Show order info
python backend/cli.py order <ORDER_NO> --status cancelled  # Update status

# === Vehicles ===
python backend/cli.py vehicle list              # List all vehicles
python backend/cli.py vehicle list --status available  # Filter by status
python backend/cli.py vehicle create --plate ABC-1234 --type van --load 2000

# === Drivers ===
python backend/cli.py driver list              # List all drivers
python backend/cli.py driver list --status active   # Filter by status

# === Expenses ===
python backend/cli.py expense record --category fuel --amount 350.0 --desc "Diesel"
python backend/cli.py expense list                     # Show recent expenses
python backend/cli.py expense list --category toll     # Filter by category

# === Dashboard ===
python backend/cli.py dashboard           # Show full summary

# === Routes ===
python backend/cli.py route <ROUTE_NO>    # Show route details

# === Users ===
python backend/cli.py user create --username alice --password secret --role operator
python backend/cli.py user list
```

---

## API Reference | API 参考

Base URL: `http://localhost:5000/api/v1`

### Authentication | 认证

**Login** -> `POST /auth/login`

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {"id": "...", "username": "admin", "role": "admin"}
}
```

Use `Authorization: Bearer <access_token>` header for all protected endpoints.

### Endpoints Summary | 端点总览

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/login` | User login | - |
| POST | `/auth/register` | Register new user | Admin |
| GET | `/auth/me` | Current user info | JWT |
| PUT | `/auth/password` | Change password | JWT |
| GET | `/orders` | List orders | JWT |
| POST | `/orders` | Create order | JWT |
| GET | `/orders/<id>` | Get order | JWT |
| PUT | `/orders/<id>` | Update order | JWT |
| POST | `/orders/<id>/confirm` | Confirm order | JWT |
| POST | `/orders/<id>/cancel` | Cancel order | JWT |
| GET | `/shipments` | List shipments | JWT |
| POST | `/shipments` | Create shipment | JWT |
| POST | `/shipments/<id>/start` | Start shipment | JWT |
| POST | `/shipments/<id>/complete` | Complete shipment | JWT |
| GET | `/vehicles` | List vehicles | JWT |
| POST | `/vehicles` | Create vehicle | Admin |
| PUT | `/vehicles/<id>/status` | Update vehicle status | Admin |
| GET | `/drivers` | List drivers | JWT |
| POST | `/drivers` | Create driver | Admin |
| PUT | `/drivers/<id>/status` | Update driver status | Admin |
| GET | `/routes` | List routes | JWT |
| POST | `/routes` | Create route | JWT |
| POST | `/routes/<id>/optimize` | Optimize waypoints | JWT |
| POST | `/routes/<id>/assign` | Assign route to shipment | JWT |
| GET | `/expenses` | List expenses | JWT |
| POST | `/expenses` | Record expense | JWT |
| GET | `/expenses/summary/daily` | Daily summary | JWT |
| GET | `/expenses/summary/monthly` | Monthly report | JWT |
| GET | `/dashboard/dashboard/stats` | Dashboard KPIs | JWT |
| GET | `/dashboard/dashboard/orders-by-status` | Orders by status | JWT |
| GET | `/dashboard/dashboard/revenue-trend` | Revenue trend | JWT |
| GET | `/dashboard/dashboard/vehicle-utilization` | Vehicle utilization | JWT |

### Order Lifecycle | 订单生命周期

```
pending -> confirmed -> picked_up -> in_transit -> delivered
    |          |
    v          v
 cancelled  cancelled
```

Orders are assigned to **Shipments** (one vehicle + driver + multiple orders).
Routes can be attached to shipments for navigation.

### Fee Calculation | 计费规则

| Component | Rule |
|-----------|------|
| First 1 kg | 1.5 |
| Each additional kg | 0.8/kg |
| Distance fee | 5-50 (city-pair based) |
| Total | Weight fee + Distance fee |

---

## Database Schema | 数据库模型

### Users (users)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| username | VARCHAR(80) | Unique username |
| password_hash | VARCHAR(255) | Hashed password |
| email | VARCHAR(120) | Unique email |
| role | VARCHAR(20) | admin / operator / driver |
| is_active | VARCHAR(20) | active / inactive |
| created_at | DATETIME | Creation timestamp |

### Orders (orders)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| order_no | VARCHAR(30) | Unique order number |
| sender_name/phone/address/city/province | - | Sender details |
| receiver_name/phone/address/city/province | - | Receiver details |
| weight | FLOAT | Package weight (kg) |
| volume | FLOAT | Package volume (cm3) |
| status | VARCHAR(20) | pending/confirmed/in_transit/delivered/cancelled |
| payment_type | VARCHAR(20) | prepaid / cod |
| cod_amount | FLOAT | Cash-on-delivery amount |
| total_fee | FLOAT | Total shipping fee |
| user_id | UUID | FK -> users.id (creator) |

### Vehicles (vehicles)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| plate_no | VARCHAR(20) | License plate (unique) |
| vehicle_type | VARCHAR(20) | van / mini_van / truck / large_truck |
| brand / model | VARCHAR(50) | Brand and model |
| load_capacity | FLOAT | Max load (kg) |
| volume_capacity | FLOAT | Max volume (m3) |
| status | VARCHAR(20) | available / on_delivery / maintenance / retired |
| fuel_type | VARCHAR(20) | gasoline / diesel / electric |
| mileage | FLOAT | Total km driven |

### Drivers (drivers)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Full name |
| phone | VARCHAR(20) | Contact phone |
| license_no | VARCHAR(50) | License number (unique) |
| license_type | VARCHAR(5) | A / B / C |
| license_expire_date | DATE | Expiry date |
| status | VARCHAR(20) | active / on_duty / on_leave / suspended |
| hire_date | DATE | Employment start date |
| salary_type | VARCHAR(20) | monthly / trip_based |
| base_salary | FLOAT | Base salary |
| user_id | UUID | FK -> users.id (optional account link) |

### Shipments (shipments)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| shipment_no | VARCHAR(30) | Unique shipment number |
| vehicle_id | UUID | FK -> vehicles.id |
| driver_id | UUID | FK -> drivers.id |
| route_id | UUID | FK -> routes.id (optional) |
| status | VARCHAR(30) | prepared / in_transit / delivered / ... |
| departure_time | DATETIME | Actual departure |
| arrival_time | DATETIME | Actual arrival |

### Routes (routes)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| route_no | VARCHAR(30) | Unique route number |
| origin_city / origin_province | VARCHAR(50) | Origin |
| destination_city / destination_province | VARCHAR(50) | Destination |
| distance | FLOAT | Distance (km) |
| estimated_time | INT | Estimated time (minutes) |
| waypoints | JSON | Array of {lat, lng, name} |
| status | VARCHAR(20) | planned / in_progress / completed |

### Expenses (expenses)

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| expense_no | VARCHAR(30) | Unique expense number |
| category | VARCHAR(30) | fuel / toll / driver_salary / maintenance / food / accommodation / other |
| amount | FLOAT | Amount |
| expense_date | DATE | Date of expense |
| vehicle_id | UUID | FK -> vehicles.id (optional) |
| driver_id | UUID | FK -> drivers.id (optional) |
| shipment_id | UUID | FK -> shipments.id (optional) |
| user_id | UUID | FK -> users.id (recorder) |

---

## Authentication | 认证

TMS uses **JWT (JSON Web Tokens)** for stateless authentication.

### Role-Based Access | 角色权限

| Role | Permissions |
|------|-------------|
| **admin** | Full access: create/delete vehicles, drivers, users; manage expenses |
| **operator** | Create orders, view all resources |
| **driver** | View assigned shipments, add tracking events |

### Token Usage | 令牌使用

```python
import requests

# Login
resp = requests.post('http://localhost:5000/api/v1/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = resp.json()['access_token']

# Authenticated request
resp = requests.get('http://localhost:5000/api/v1/orders',
    headers={'Authorization': f'Bearer {token}'})
```

---

## Testing | 测试

```bash
# Run all tests
pytest tests -v

# Run with coverage
pytest tests -v --cov=. --cov-report=html

# Run specific test file
pytest tests/test_models.py -v

# Run specific test class
pytest tests/test_services.py::TestOrderServiceCalculateFee -v

# Run with markers
pytest tests -v -k "order"
```

### Test Structure | 测试结构

```
tests/
├── conftest.py         # Fixtures: app, client, auth headers, sample data
├── test_models.py      # Model creation, validation, to_dict(), repr()
├── test_services.py    # Service business logic (in-memory, no DB)
└── test_api.py         # HTTP endpoint tests via Flask test client
```

---

## Configuration | 配置

### Environment Variables | 环境变量

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `tms-secret-key-...` | Flask secret key |
| `JWT_SECRET_KEY` | `jwt-secret-key-...` | JWT signing key |
| `DATABASE_URL` | `sqlite:///tms.db` | Production DB URI |
| `DEV_DATABASE_URL` | `sqlite:///tms_dev.db` | Development DB URI |

### Configuration Classes | 配置类

| Config | Use |
|--------|-----|
| `Config` | Base configuration |
| `DevelopmentConfig` | `FLASK_ENV=development` |
| `TestingConfig` | `pytest`, in-memory SQLite |
| `ProductionConfig` | Production deployment |

### Switching Config | 切换配置

```python
# In run.py or app factory
app = create_app('development')   # or 'production', 'testing'
```

---

## License

MIT License - see LICENSE file for details.
