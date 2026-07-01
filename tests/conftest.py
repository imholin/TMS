"""
conftest.py — pytest fixtures for TMS test suite.
"""
import os
import sys
import pytest
from datetime import date

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.app import create_app
from backend.extensions import db
from backend.models import User, Vehicle, Driver, Order, Route, Expense, Shipment


@pytest.fixture(scope='function')
def app():
    """Create Flask app configured for testing (in-memory SQLite)."""
    _app = create_app('testing')
    with _app.app_context():
        db.create_all()
    yield _app
    with _app.app_context():
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        db.drop_all()


@pytest.fixture(scope='function')
def db_(app):
    """DB session with app context; tables cleared before each test."""
    with app.app_context():
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        yield db


@pytest.fixture(scope='function')
def client(app):
    """Flask test client for each test function."""
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Auth fixtures
# ---------------------------------------------------------------------------
def _get_auth_headers(client, username, password):
    resp = client.post('/api/v1/auth/login', json={
        'username': username,
        'password': password,
    })
    if resp.status_code == 200:
        token = resp.get_json()['access_token']
        return {'Authorization': f'Bearer {token}'}
    return {}


@pytest.fixture
def admin_user(db_):
    """Create and return an admin User; password is 'testpass'."""
    u = User(username='admin_test', password='testpass', email='admin@test.com', role='admin')
    db_.session.add(u); db_.session.commit()
    return u


@pytest.fixture
def admin_auth(client, admin_user):
    """Return Authorization headers for admin."""
    return _get_auth_headers(client, 'admin_test', 'testpass')


@pytest.fixture
def operator_user(db_):
    """Create and return an operator User."""
    u = User(username='op_test', password='testpass', email='op@test.com', role='operator')
    db_.session.add(u); db_.session.commit()
    return u


@pytest.fixture
def operator_auth(client, operator_user):
    """Return Authorization headers for operator."""
    return _get_auth_headers(client, 'op_test', 'testpass')


@pytest.fixture
def driver_user(db_):
    """Create and return a driver User."""
    u = User(username='drv_test', password='testpass', email='drv@test.com', role='driver')
    db_.session.add(u); db_.session.commit()
    return u


@pytest.fixture
def driver_auth(client, driver_user):
    """Return Authorization headers for driver."""
    return _get_auth_headers(client, 'drv_test', 'testpass')


# ---------------------------------------------------------------------------
# Resource fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_vehicle(db_):
    v = Vehicle(
        plate_no='TEST-001', vehicle_type='van',
        load_capacity=2000.0, volume_capacity=10.0,
        brand='五菱', model='宏光',
    )
    db_.session.add(v); db_.session.commit()
    return v


@pytest.fixture
def sample_driver(db_):
    d = Driver(
        name='张测试', phone='13800000000',
        license_no='L310000000', license_type='B',
        license_expire_date=date(2030, 12, 31),
    )
    db_.session.add(d); db_.session.commit()
    return d


@pytest.fixture
def sample_route(db_, sample_driver):
    r = Route(
        route_no='R001',
        origin_city='上海', origin_province='上海',
        destination_city='北京', destination_province='北京',
        distance=1200.0, estimated_time=720,
    )
    db_.session.add(r); db_.session.commit()
    return r


@pytest.fixture
def sample_order(db_, operator_user):
    o = Order(
        sender_name='发件人', sender_phone='13800000001',
        sender_address='上海市浦东新区', sender_city='上海', sender_province='上海',
        receiver_name='收件人', receiver_phone='13900000001',
        receiver_address='北京市朝阳区', receiver_city='北京', receiver_province='北京',
        weight=5.0, volume=1000.0,
        user_id=operator_user.id,
    )
    db_.session.add(o); db_.session.commit()
    return o


@pytest.fixture
def sample_confirmed_order(db_, operator_user):
    o = Order(
        sender_name='确认发件人', sender_phone='13800000002',
        sender_address='上海市', sender_city='上海', sender_province='上海',
        receiver_name='确认收件人', receiver_phone='13900000002',
        receiver_address='北京市', receiver_city='北京', receiver_province='北京',
        weight=10.0, volume=2000.0,
        status='confirmed',
        user_id=operator_user.id,
    )
    db_.session.add(o); db_.session.commit()
    return o


@pytest.fixture
def sample_shipment(db_, sample_vehicle, sample_driver):
    s = Shipment(
        vehicle_id=sample_vehicle.id,
        driver_id=sample_driver.id,
    )
    db_.session.add(s); db_.session.commit()
    return s


@pytest.fixture
def sample_expense(db_, operator_user, sample_vehicle):
    e = Expense(
        category='fuel', amount=300.0,
        vehicle_id=sample_vehicle.id,
        user_id=operator_user.id,
        expense_date=date.today(),
    )
    db_.session.add(e); db_.session.commit()
    return e
