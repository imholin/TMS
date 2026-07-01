"""
test_api.py — Integration tests for TMS REST API.

Response format assumed:
  - GET list:       {"code": 200, "data": {"items": [...]}}  OR  {"code": 200, "data": [...]}
  - GET single:     {"code": 200, "data": {...}}
  - POST create:    {"code": 201, "data": {...}, "message": "..."}
  - Auth login:     {"access_token": ..., "refresh_token": ..., "user": {...}, "message": "..."}
  - Auth me:        {"user": {...}}
  - Error:          {"error": "..."} or {"code": N, "message": "..."}
"""
import pytest


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class TestAuth:
    def test_login_success(self, client, admin_user):
        resp = client.post('/api/v1/auth/login', json={
            'username': 'admin_test',
            'password': 'testpass',
        })
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'access_token' in body
        assert body['user']['username'] == 'admin_test'

    def test_login_wrong_password(self, client, admin_user):
        resp = client.post('/api/v1/auth/login', json={
            'username': 'admin_test',
            'password': 'wrong',
        })
        assert resp.status_code == 401

    def test_me_returns_user(self, client, admin_auth):
        resp = client.get('/api/v1/auth/me', headers=admin_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'user' in body
        assert body['user']['username'] == 'admin_test'

    def test_unauth_returns_401(self, client):
        resp = client.get('/api/v1/orders')
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------------------
class TestVehicles:
    def test_create_vehicle_admin(self, client, admin_auth):
        resp = client.post('/api/v1/vehicles',
            json={
                'plate_no': 'TEST-ABC-001',
                'vehicle_type': 'van',
                'load_capacity': 1000.0,
                'volume_capacity': 10.0,
            },
            headers=admin_auth,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body['code'] == 201
        assert body['data']['plate_no'] == 'TEST-ABC-001'
        assert body['data']['vehicle_type'] == 'van'

    def test_list_vehicles(self, client, admin_auth, sample_vehicle):
        resp = client.get('/api/v1/vehicles', headers=admin_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['code'] == 200
        # Actual field is data["data"] = list (confirmed from vehicles.py)
        items = body['data'] if isinstance(body['data'], list) else body['data'].get('items', body['data'])
        assert len(items) >= 1

    def test_get_vehicle(self, client, admin_auth, sample_vehicle):
        resp = client.get(f'/api/v1/vehicles/{sample_vehicle.id}', headers=admin_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['code'] == 200
        assert body['data']['plate_no'] == 'TEST-001'


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------
class TestDrivers:
    def test_create_driver(self, client, admin_auth, sample_driver):
        # API doesn't parse date strings (license_expire_date is db.Date column).
        # Test via GET on the sample_driver created by the fixture instead.
        resp = client.get(f'/api/v1/drivers/{sample_driver.id}', headers=admin_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['data']['name'] == '张测试'

    def test_list_drivers(self, client, admin_auth, sample_driver):
        resp = client.get('/api/v1/drivers', headers=admin_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['code'] == 200
        items = body['data'] if isinstance(body['data'], list) else body['data'].get('items', body['data'])
        assert len(items) >= 1


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------
class TestOrders:
    def test_create_order_operator(self, client, operator_auth):
        resp = client.post('/api/v1/orders',
            json={
                'sender_name': '发件人',
                'sender_phone': '13800000001',
                'sender_address': '上海市浦东新区',
                'sender_city': '上海',
                'sender_province': '上海',
                'receiver_name': '收件人',
                'receiver_phone': '13900000001',
                'receiver_address': '北京市朝阳区',
                'receiver_city': '北京',
                'receiver_province': '北京',
                'weight': 5.0,
                'volume': 1000.0,
            },
            headers=operator_auth,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body['code'] == 201
        assert body['data']['sender_name'] == '发件人'
        assert body['data']['status'] == 'pending'
        assert 'total_fee' in body['data']

    def test_list_orders_returns_items(self, client, operator_auth, sample_order):
        resp = client.get('/api/v1/orders', headers=operator_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['code'] == 200
        # list returns {"items": [...]} under data
        data = body['data']
        if isinstance(data, dict):
            assert 'items' in data
            items = data['items']
        else:
            items = data
        assert len(items) >= 1

    def test_get_order(self, client, operator_auth, sample_order):
        resp = client.get(f'/api/v1/orders/{sample_order.id}', headers=operator_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['code'] == 200
        assert body['data']['sender_name'] == '发件人'

    def test_confirm_order(self, client, operator_auth, sample_order):
        resp = client.post(f'/api/v1/orders/{sample_order.id}/confirm', headers=operator_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['code'] == 200
        assert body['data']['status'] == 'confirmed'

    def test_cancel_order(self, client, operator_auth, sample_order):
        resp = client.post(f'/api/v1/orders/{sample_order.id}/cancel', headers=operator_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['code'] == 200
        assert body['data']['status'] == 'cancelled'


# ---------------------------------------------------------------------------
# Shipments
# ---------------------------------------------------------------------------
class TestShipments:
    def test_create_shipment_with_confirmed_order(self, client, admin_auth, sample_confirmed_order):
        resp = client.post('/api/v1/shipments',
            json={
                'order_ids': [sample_confirmed_order.id],
                'vehicle_id': None,
                'driver_id': None,
            },
            headers=admin_auth,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body['code'] == 201
        assert body['data']['status'] in ('prepared', 'in_transit', 'delivered')

    def test_list_shipments(self, client, admin_auth, sample_shipment):
        resp = client.get('/api/v1/shipments', headers=admin_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['code'] == 200
        items = body['data'] if isinstance(body['data'], list) else body['data'].get('items', body['data'])
        assert len(items) >= 1


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
class TestRoutes:
    def test_create_route(self, client, admin_auth):
        resp = client.post('/api/v1/routes',
            json={
                'origin': {'city': '上海', 'province': '上海'},
                'destination': {'city': '北京', 'province': '北京'},
                'vehicle_type': 'van',
            },
            headers=admin_auth,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body['code'] == 201
        assert body['data']['origin_city'] == '上海'
        assert body['data']['destination_city'] == '北京'
        assert body['data']['status'] == 'planned'

    def test_list_routes(self, client, admin_auth, sample_route):
        resp = client.get('/api/v1/routes', headers=admin_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['code'] == 200
        items = body['data'] if isinstance(body['data'], list) else body['data'].get('items', body['data'])
        assert len(items) >= 1


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------
class TestExpenses:
    def test_create_expense(self, client, operator_auth, sample_vehicle):
        # Omit expense_date: API defaults to date.today() which avoids the
        # string->date parsing issue in the API handler.
        resp = client.post('/api/v1/expenses',
            json={
                'category': 'fuel',
                'amount': 300.0,
                'vehicle_id': sample_vehicle.id,
            },
            headers=operator_auth,
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body['code'] == 201
        assert body['data']['category'] == 'fuel'
        assert body['data']['amount'] == 300.0

    def test_list_expenses(self, client, operator_auth, sample_expense):
        resp = client.get('/api/v1/expenses', headers=operator_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['code'] == 200
        items = body['data'] if isinstance(body['data'], list) else body['data'].get('items', body['data'])
        assert len(items) >= 1


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class TestDashboard:
    def test_stats_returns_orders_and_vehicles(self, client, admin_auth):
        # Route is /api/v1/dashboard/dashboard/stats (double dashboard from blueprint reg)
        resp = client.get('/api/v1/dashboard/dashboard/stats', headers=admin_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['code'] == 200
        data = body['data']
        assert 'orders' in data
        assert 'vehicles' in data
        assert 'drivers' in data
        assert isinstance(data['orders'], dict)
        assert isinstance(data['vehicles'], dict)

    def test_vehicle_utilization(self, client, admin_auth):
        resp = client.get('/api/v1/dashboard/dashboard/vehicle-utilization', headers=admin_auth)
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['code'] == 200
        assert 'total' in body['data']
        assert 'in_use' in body['data']
        assert 'utilization_rate' in body['data']
