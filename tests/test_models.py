"""
tests/test_models.py — SQLAlchemy model unit tests.
Uses db_ fixture (correct db instance + app context from conftest.py).
"""
import pytest
from datetime import date


class TestUserModel:
    def test_password_hashing(self, db_):
        from backend.models import User
        user = User(username='user_hash', password='mysecret123', role='operator')
        db_.session.add(user); db_.session.commit()
        assert user.password_hash != 'mysecret123'
        assert len(user.password_hash) > 20
        assert user.check_password('mysecret123') is True
        assert user.check_password('wrong') is False

    def test_different_passwords_different_hashes(self, db_):
        from backend.models import User
        u1 = User(username='u1', password='same', role='operator')
        u2 = User(username='u2', password='same', role='operator')
        db_.session.add_all([u1, u2]); db_.session.commit()
        assert u1.password_hash != u2.password_hash

    def test_user_roles(self, db_):
        from backend.models import User
        admin = User(username='t_adm', password='p', role='admin')
        op = User(username='t_op', password='p', role='operator')
        drv = User(username='t_drv', password='p', role='driver')
        db_.session.add_all([admin, op, drv]); db_.session.commit()
        assert admin.is_admin is True; assert admin.is_operator is False
        assert op.is_admin is False; assert op.is_operator is True
        assert drv.is_driver is True

    def test_to_dict_excludes_password(self, db_):
        from backend.models import User
        u = User(username='u_dict', password='p', email='d@t.com', role='operator')
        db_.session.add(u); db_.session.commit()
        data = u.to_dict()
        assert 'password_hash' not in data
        assert data['username'] == 'u_dict'

    def test_invalid_role_defaults_to_operator(self, db_):
        from backend.models import User
        u = User(username='bad_role', password='p', role='superadmin')
        db_.session.add(u); db_.session.commit()
        assert u.role == User.ROLE_OPERATOR

    def test_unique_username(self, db_):
        from backend.models import User
        from sqlalchemy.exc import IntegrityError
        u1 = User(username='uniq_u', password='p', role='operator')
        db_.session.add(u1); db_.session.commit()
        u2 = User(username='uniq_u', password='p', role='operator')
        db_.session.add(u2)
        with pytest.raises(IntegrityError):
            db_.session.commit()
        db_.session.rollback()


class TestOrderModel:
    def _make_user(self, db_, name):
        from backend.models import User
        u = User(username=name, password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        return u

    def _make_order(self, db_, user, **kwargs):
        from backend.models import Order
        defaults = dict(
            sender_name='S', sender_phone='13800000000',
            sender_address='SA', sender_city='SC', sender_province='SP',
            receiver_name='R', receiver_phone='13900000000',
            receiver_address='RA', receiver_city='RC', receiver_province='RP',
            weight=1.0, volume=500.0, user_id=user.id,
        )
        defaults.update(kwargs)
        o = Order(**defaults)
        db_.session.add(o); db_.session.commit()
        return o

    def test_order_no_generation(self, db_):
        u = self._make_user(db_, 'ord_u1')
        o = self._make_order(db_, u)
        assert o.order_no.startswith('ORD')
        assert len(o.order_no) >= 14

    def test_order_no_unique(self, db_):
        u = self._make_user(db_, 'ord_u2')
        orders = [self._make_order(db_, u, sender_phone=f'138000{i:04d}') for i in range(5)]
        nos = [o.order_no for o in orders]
        assert len(nos) == len(set(nos))

    def test_default_status_pending(self, db_):
        u = self._make_user(db_, 'ord_u3')
        o = self._make_order(db_, u)
        assert o.status == 'pending'

    def test_to_dict_fields(self, db_):
        u = self._make_user(db_, 'ord_u4')
        o = self._make_order(db_, u, sender_name='Alice', weight=3.5)
        data = o.to_dict()
        assert data['sender_name'] == 'Alice'
        assert data['weight'] == 3.5


class TestShipmentModel:
    def _make_vehicle_driver(self, db_, suffix=''):
        from backend.models import Vehicle, Driver
        v = Vehicle(
            plate_no=f'PL{suffix}', vehicle_type='van',
            load_capacity=2000.0, volume_capacity=12.0,
        )
        d = Driver(
            name=f'Drv{suffix}', phone=f'138000{suffix}',
            license_no=f'L{suffix}', license_type='B',
            license_expire_date=date(2030, 1, 1),
        )
        db_.session.add_all([v, d]); db_.session.commit()
        return v, d

    def test_shipment_number_prefix(self, db_):
        v, d = self._make_vehicle_driver(db_, 'SH1')
        from backend.models import Shipment
        s = Shipment(vehicle_id=v.id, driver_id=d.id)
        db_.session.add(s); db_.session.commit()
        assert s.shipment_no.startswith('SHP')

    def test_shipment_order_assignment(self, db_):
        from backend.models import User, Order, Shipment
        u = User(username='ship_u1', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        v, d = self._make_vehicle_driver(db_, 'SH2')
        o = Order(
            sender_name='S', sender_phone='13800000000',
            sender_address='SA', sender_city='SC', sender_province='SP',
            receiver_name='R', receiver_phone='13900000000',
            receiver_address='RA', receiver_city='RC', receiver_province='RP',
            weight=1.0, volume=500.0, user_id=u.id,
        )
        db_.session.add(o); db_.session.commit()
        s = Shipment(vehicle_id=v.id, driver_id=d.id)
        db_.session.add(s); db_.session.commit()
        s.orders.append(o); db_.session.commit()
        assert o in s.orders

    def test_shipment_status_transitions(self, db_):
        from backend.models import Shipment
        v, d = self._make_vehicle_driver(db_, 'SH3')
        s = Shipment(vehicle_id=v.id, driver_id=d.id)
        db_.session.add(s); db_.session.commit()
        assert s.status == 'prepared'
        s.status = 'in_transit'
        db_.session.commit()
        assert s.status == 'in_transit'


class TestVehicleModel:
    def test_vehicle_defaults(self, db_):
        from backend.models import Vehicle
        v = Vehicle(plate_no='V001', vehicle_type='truck',
                    load_capacity=5000.0, volume_capacity=25.0)
        db_.session.add(v); db_.session.commit()
        assert v.status == Vehicle.STATUS_AVAILABLE
        assert v.mileage == 0.0

    def test_unique_plate(self, db_):
        from backend.models import Vehicle
        from sqlalchemy.exc import IntegrityError
        v1 = Vehicle(plate_no='DUPA', vehicle_type='van', load_capacity=1000.0, volume_capacity=5.0)
        db_.session.add(v1); db_.session.commit()
        v2 = Vehicle(plate_no='DUPA', vehicle_type='truck', load_capacity=3000.0, volume_capacity=15.0)
        db_.session.add(v2)
        with pytest.raises(IntegrityError):
            db_.session.commit()
        db_.session.rollback()

    def test_to_dict_fields(self, db_):
        from backend.models import Vehicle
        v = Vehicle(plate_no='VDICT', vehicle_type='mini_van',
                    brand='金杯', model='大海狮',
                    load_capacity=1500.0, volume_capacity=8.0)
        db_.session.add(v); db_.session.commit()
        data = v.to_dict()
        assert data['plate_no'] == 'VDICT'
        assert data['brand'] == '金杯'


class TestDriverModel:
    def test_driver_creation(self, db_):
        from backend.models import Driver
        d = Driver(name='王小明', phone='13812345678',
                   license_no='L310000000', license_type='B',
                   license_expire_date=date(2028, 12, 31),
                   base_salary=6000.0, status='active')
        db_.session.add(d); db_.session.commit()
        assert d.is_license_expired is False
        assert d.license_days_remaining > 0

    def test_license_expired(self, db_):
        from backend.models import Driver
        d = Driver(name='过期', phone='13899999999',
                   license_no='L000000001', license_type='C',
                   license_expire_date=date(2020, 1, 1))
        db_.session.add(d); db_.session.commit()
        assert d.is_license_expired is True
        assert d.license_days_remaining < 0

    def test_driver_vehicle_assignment(self, db_):
        from backend.models import Driver, Vehicle
        v = Vehicle(plate_no='VA2', vehicle_type='van', load_capacity=2000.0, volume_capacity=10.0)
        db_.session.add(v); db_.session.commit()
        d = Driver(name='分配', phone='13800000111',
                   license_no='L330000001', license_type='B',
                   license_expire_date=date(2029, 1, 1))
        db_.session.add(d); db_.session.commit()
        d.vehicle_id = v.id
        db_.session.commit()
        assert d.vehicle_id == v.id


class TestExpenseModel:
    def _make_user(self, db_, name):
        from backend.models import User
        u = User(username=name, password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        return u

    def test_expense_number_prefix(self, db_):
        from backend.models import Expense
        u = self._make_user(db_, 'exp_u1')
        e = Expense(category='fuel', amount=300.0, user_id=u.id)
        db_.session.add(e); db_.session.commit()
        assert e.expense_no.startswith('EXP')

    def test_expense_valid_categories(self, db_):
        from backend.models import Expense
        u = self._make_user(db_, 'exp_u2')
        for cat in Expense.VALID_CATEGORIES:
            e = Expense(category=cat, amount=10.0, user_id=u.id)
            db_.session.add(e)
        db_.session.commit()
        stored = Expense.query.filter(
            Expense.category.in_(Expense.VALID_CATEGORIES)
        ).all()
        assert len(stored) == len(Expense.VALID_CATEGORIES)

    def test_expense_amounts(self, db_):
        from backend.models import Expense
        u = self._make_user(db_, 'exp_u3')
        for amt in [0.01, 99.99, 10000.0]:
            e = Expense(category='fuel', amount=amt, user_id=u.id)
            db_.session.add(e)
        db_.session.commit()
        assert Expense.query.count() >= 3
