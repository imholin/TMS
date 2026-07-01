"""
test_services.py — Unit tests for TMS service layer.

All tests use the `db_` fixture which provides app context + correct db instance.
For services that need a user_id, create a User inside the test first.
"""
import pytest
from datetime import date

from backend.models import User, Order, Vehicle, Driver, Route, Expense, Shipment
from backend.services.order_service import OrderService
from backend.services.route_service import RouteService
from backend.services.billing_service import BillingService
from backend.services.tracking_service import TrackingService


# ---------------------------------------------------------------------------
# OrderService.calculate_fee
# ---------------------------------------------------------------------------
class TestOrderCalculateFee:
    def test_basic_fee(self):
        result = OrderService.calculate_fee(5.0, '上海', '北京')
        assert result['total_fee'] > 0
        assert result['weight'] == 5.0

    def test_single_kg(self):
        result = OrderService.calculate_fee(1.0, '上海', '北京')
        assert result['first_kg_fee'] == 1.5
        assert result['weight_fee'] == 1.5

    def test_zero_weight_raises(self):
        with pytest.raises(ValueError):
            OrderService.calculate_fee(0, '上海', '北京')

    def test_negative_weight_raises(self):
        with pytest.raises(ValueError):
            OrderService.calculate_fee(-1.0, '上海', '北京')


# ---------------------------------------------------------------------------
# OrderService.create_order
# ---------------------------------------------------------------------------
class TestOrderCreate:
    def test_sets_pending_status(self, db_):
        u = User(username='svc_order_u1', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        data = {
            'sender_name': '发', 'sender_phone': '13800000000',
            'sender_address': '上海', 'sender_city': '上海', 'sender_province': '上海',
            'receiver_name': '收', 'receiver_phone': '13900000000',
            'receiver_address': '北京', 'receiver_city': '北京', 'receiver_province': '北京',
            'weight': 5.0, 'volume': 1000.0,
        }
        order = OrderService.create_order(data, u.id)
        assert order.status == 'pending'

    def test_calculates_fee(self, db_):
        u = User(username='svc_order_u2', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        data = {
            'sender_name': '发', 'sender_phone': '13800000000',
            'sender_address': '上海', 'sender_city': '上海', 'sender_province': '上海',
            'receiver_name': '收', 'receiver_phone': '13900000000',
            'receiver_address': '北京', 'receiver_city': '北京', 'receiver_province': '北京',
            'weight': 5.0,
        }
        order = OrderService.create_order(data, u.id)
        assert order.total_fee is not None
        assert order.total_fee > 0

    def test_missing_required_field_raises(self, db_):
        u = User(username='svc_order_u3', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        data = {
            'sender_name': '发',
            # missing sender_phone, etc.
            'receiver_name': '收',
            'weight': 5.0,
        }
        with pytest.raises(ValueError):
            OrderService.create_order(data, u.id)


# ---------------------------------------------------------------------------
# OrderService.confirm_order
# ---------------------------------------------------------------------------
class TestOrderConfirm:
    def test_confirm_pending_ok(self, db_):
        u = User(username='svc_order_u4', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        data = {
            'sender_name': '发', 'sender_phone': '13800000000',
            'sender_address': '上海', 'sender_city': '上海', 'sender_province': '上海',
            'receiver_name': '收', 'receiver_phone': '13900000000',
            'receiver_address': '北京', 'receiver_city': '北京', 'receiver_province': '北京',
            'weight': 5.0,
        }
        order = OrderService.create_order(data, u.id)
        confirmed = OrderService.confirm_order(order.id)
        assert confirmed.status == 'confirmed'

    def test_confirm_non_pending_raises(self, db_):
        u = User(username='svc_order_u5', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        o = Order(
            sender_name='发', sender_phone='13800000000',
            sender_address='上海', sender_city='上海', sender_province='上海',
            receiver_name='收', receiver_phone='13900000000',
            receiver_address='北京', receiver_city='北京', receiver_province='北京',
            weight=5.0, volume=1000.0, status='delivered', user_id=u.id,
        )
        db_.session.add(o); db_.session.commit()
        with pytest.raises(ValueError):
            OrderService.confirm_order(o.id)


# ---------------------------------------------------------------------------
# OrderService.cancel_order
# ---------------------------------------------------------------------------
class TestOrderCancel:
    def test_cancel_pending_ok(self, db_):
        u = User(username='svc_order_u6', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        data = {
            'sender_name': '发', 'sender_phone': '13800000000',
            'sender_address': '上海', 'sender_city': '上海', 'sender_province': '上海',
            'receiver_name': '收', 'receiver_phone': '13900000000',
            'receiver_address': '北京', 'receiver_city': '北京', 'receiver_province': '北京',
            'weight': 5.0,
        }
        order = OrderService.create_order(data, u.id)
        cancelled = OrderService.cancel_order(order.id)
        assert cancelled.status == 'cancelled'

    def test_cancel_in_transit_raises(self, db_):
        u = User(username='svc_order_u7', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        o = Order(
            sender_name='发', sender_phone='13800000000',
            sender_address='上海', sender_city='上海', sender_province='上海',
            receiver_name='收', receiver_phone='13900000000',
            receiver_address='北京', receiver_city='北京', receiver_province='北京',
            weight=5.0, volume=1000.0, status='in_transit', user_id=u.id,
        )
        db_.session.add(o); db_.session.commit()
        with pytest.raises(ValueError):
            OrderService.cancel_order(o.id)


# ---------------------------------------------------------------------------
# OrderService.get_order / get_orders
# ---------------------------------------------------------------------------
class TestOrderGet:
    def test_get_order_returns_order(self, db_):
        u = User(username='svc_order_u8', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        data = {
            'sender_name': '发', 'sender_phone': '13800000000',
            'sender_address': '上海', 'sender_city': '上海', 'sender_province': '上海',
            'receiver_name': '收', 'receiver_phone': '13900000000',
            'receiver_address': '北京', 'receiver_city': '北京', 'receiver_province': '北京',
            'weight': 5.0,
        }
        created = OrderService.create_order(data, u.id)
        fetched = OrderService.get_order(created.id)
        assert fetched.id == created.id

    def test_get_order_not_found_raises(self, app):
        with app.app_context():
            with pytest.raises(KeyError):
                OrderService.get_order('non-existent-id')

    def test_get_orders_filter_by_status(self, db_):
        u = User(username='svc_order_u9', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        data = {
            'sender_name': '发', 'sender_phone': '13800000000',
            'sender_address': '上海', 'sender_city': '上海', 'sender_province': '上海',
            'receiver_name': '收', 'receiver_phone': '13900000000',
            'receiver_address': '北京', 'receiver_city': '北京', 'receiver_province': '北京',
            'weight': 5.0,
        }
        OrderService.create_order(data, u.id)
        items, total = OrderService.get_orders({'status': 'pending'})
        assert total >= 1
        assert all(o.status == 'pending' for o in items)

    def test_get_orders_pagination(self, db_):
        u = User(username='svc_order_u10', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        data = {
            'sender_name': '发', 'sender_phone': '13800000000',
            'sender_address': '上海', 'sender_city': '上海', 'sender_province': '上海',
            'receiver_name': '收', 'receiver_phone': '13900000000',
            'receiver_address': '北京', 'receiver_city': '北京', 'receiver_province': '北京',
            'weight': 5.0,
        }
        OrderService.create_order(data, u.id)
        items, total = OrderService.get_orders({'page': 1, 'per_page': 5})
        assert len(items) >= 1
        assert total >= 1


# ---------------------------------------------------------------------------
# RouteService.haversine
# ---------------------------------------------------------------------------
class TestHaversine:
    def test_same_point_is_zero(self):
        d = RouteService.haversine(31.2, 121.5, 31.2, 121.5)
        assert d == 0.0

    def test_known_distance_shanghai_beijing(self):
        # Shanghai approx 31.2N 121.5E, Beijing approx 39.9N 116.4E
        d = RouteService.haversine(31.2, 121.5, 39.9, 116.4)
        assert 1050 < d < 1200  # ~1100 km

    def test_intermediate_waypoints(self):
        # Distance via intermediate point should be >= direct
        d_direct = RouteService.haversine(0, 0, 10, 10)
        d_via = RouteService.haversine(0, 0, 5, 5) + RouteService.haversine(5, 5, 10, 10)
        assert d_via >= d_direct - 1  # allow small floating point tolerance


# ---------------------------------------------------------------------------
# RouteService.estimate_delivery_time
# ---------------------------------------------------------------------------
class TestEstimateDeliveryTime:
    def test_van_speed(self):
        # 60 km/h -> 120 km takes 120 minutes
        mins = RouteService.estimate_delivery_time(120.0, 'van')
        assert mins == 120

    def test_truck_speed(self):
        # 50 km/h -> 100 km takes 120 minutes
        mins = RouteService.estimate_delivery_time(100.0, 'truck')
        assert mins == 120

    def test_unknown_vehicle_type(self):
        # Unknown type falls back to 60 km/h
        mins = RouteService.estimate_delivery_time(60.0, 'unknown_type')
        assert mins == 60


# ---------------------------------------------------------------------------
# RouteService.create_route
# ---------------------------------------------------------------------------
class TestRouteCreate:
    def test_sets_planned_status(self, db_):
        data = {
            'origin': {'city': '上海', 'province': '上海'},
            'destination': {'city': '北京', 'province': '北京'},
            'vehicle_type': 'van',
        }
        route = RouteService.create_route(data)
        assert route.status == 'planned'

    def test_sets_origin_and_destination(self, db_):
        data = {
            'origin': {'city': '上海', 'province': '上海'},
            'destination': {'city': '北京', 'province': '北京'},
        }
        route = RouteService.create_route(data)
        assert route.origin_city == '上海'
        assert route.destination_city == '北京'


# ---------------------------------------------------------------------------
# RouteService.assign_route_to_shipment
# ---------------------------------------------------------------------------
class TestAssignRouteToShipment:
    def test_assign_planned_route_ok(self, db_):
        v = Vehicle(plate_no='TRK-001', vehicle_type='truck',
                    load_capacity=5000.0, volume_capacity=30.0)
        db_.session.add(v); db_.session.commit()
        d = Driver(name='司', phone='13800000000', license_no='L1', license_type='B',
                   license_expire_date=date(2030, 12, 31))
        db_.session.add(d); db_.session.commit()
        s = Shipment(vehicle_id=v.id, driver_id=d.id, status='prepared')
        db_.session.add(s); db_.session.commit()
        route = Route(
            route_no='R001', origin_city='上海', origin_province='上海',
            destination_city='北京', destination_province='北京',
            distance=1000.0, estimated_time=600, status='planned',
        )
        db_.session.add(route); db_.session.commit()
        result = RouteService.assign_route_to_shipment(route.id, s.id)
        assert result.status == 'in_progress'

    def test_assign_non_planned_route_raises(self, db_):
        v = Vehicle(plate_no='TRK-002', vehicle_type='truck',
                    load_capacity=5000.0, volume_capacity=30.0)
        db_.session.add(v); db_.session.commit()
        d = Driver(name='司2', phone='13800000001', license_no='L2', license_type='B',
                   license_expire_date=date(2030, 12, 31))
        db_.session.add(d); db_.session.commit()
        s = Shipment(vehicle_id=v.id, driver_id=d.id, status='prepared')
        db_.session.add(s); db_.session.commit()
        route = Route(
            route_no='R002', origin_city='上海', origin_province='上海',
            destination_city='广州', destination_province='广东',
            distance=1800.0, estimated_time=1200, status='completed',
        )
        db_.session.add(route); db_.session.commit()
        with pytest.raises(ValueError):
            RouteService.assign_route_to_shipment(route.id, s.id)


# ---------------------------------------------------------------------------
# BillingService.record_expense
# ---------------------------------------------------------------------------
class TestRecordExpense:
    def test_creates_expense(self, db_):
        u = User(username='svc_exp_u1', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        data = {'category': 'fuel', 'amount': 200.0}
        expense = BillingService.record_expense(data, u.id)
        assert expense.category == 'fuel'
        assert expense.amount == 200.0

    def test_invalid_category_raises(self, db_):
        u = User(username='svc_exp_u2', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        data = {'category': 'invalid_cat', 'amount': 100.0}
        with pytest.raises(ValueError):
            BillingService.record_expense(data, u.id)

    def test_zero_amount_raises(self, db_):
        u = User(username='svc_exp_u3', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        data = {'category': 'fuel', 'amount': 0.0}
        with pytest.raises(ValueError):
            BillingService.record_expense(data, u.id)

    def test_negative_amount_raises(self, db_):
        u = User(username='svc_exp_u4', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        data = {'category': 'fuel', 'amount': -50.0}
        with pytest.raises(ValueError):
            BillingService.record_expense(data, u.id)



# ---------------------------------------------------------------------------
# BillingService.get_daily_summary
# ---------------------------------------------------------------------------
class TestBillingDailySummary:
    def test_empty_day(self, db_):
        result = BillingService.get_daily_summary('2099-01-01')
        assert result['total'] == 0.0
        assert result['count'] == 0

    def test_aggregates_by_category(self, db_):
        u = User(username='svc_bill_u3', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        BillingService.record_expense({'category': 'fuel', 'amount': 100.0, 'expense_date': date(2026, 7, 1)}, u.id)
        BillingService.record_expense({'category': 'fuel', 'amount': 50.0, 'expense_date': date(2026, 7, 1)}, u.id)
        BillingService.record_expense({'category': 'toll', 'amount': 30.0, 'expense_date': date(2026, 7, 1)}, u.id)
        result = BillingService.get_daily_summary('2026-07-01')
        assert result['total'] == 180.0
        assert result['count'] == 3
        assert result['by_category']['fuel']['total'] == 150.0
        assert result['by_category']['toll']['total'] == 30.0


# ---------------------------------------------------------------------------
# BillingService.get_monthly_report
# ---------------------------------------------------------------------------
class TestBillingMonthlyReport:
    def test_empty_month(self, db_):
        result = BillingService.get_monthly_report(2099, 1)
        assert result['total'] == 0.0
        assert result['count'] == 0

    def test_with_data(self, db_):
        u = User(username='svc_bill_u4', password='p', role='operator')
        db_.session.add(u); db_.session.commit()
        BillingService.record_expense({'category': 'fuel', 'amount': 200.0, 'expense_date': date(2026, 6, 15)}, u.id)
        result = BillingService.get_monthly_report(2026, 6)
        assert result['total'] == 200.0
        assert result['count'] == 1
        assert result['by_category']['fuel']['total'] == 200.0


# ---------------------------------------------------------------------------
# TrackingService.record_event
# ---------------------------------------------------------------------------
class TestTrackingRecordEvent:
    def test_returns_dict(self, db_):
        v = Vehicle(plate_no='TRK-TRK1', vehicle_type='van',
                    load_capacity=1000.0, volume_capacity=10.0)
        db_.session.add(v); db_.session.commit()
        d = Driver(name='追踪司', phone='13800000010', license_no='LT1', license_type='B',
                   license_expire_date=date(2030, 12, 31))
        db_.session.add(d); db_.session.commit()
        s = Shipment(vehicle_id=v.id, driver_id=d.id)
        db_.session.add(s); db_.session.commit()
        result = TrackingService.record_event(s.id, 'departed', '上海', '出发了')
        assert isinstance(result, dict)
        assert result['event_type'] == 'departed'
        assert result['location'] == '上海'

    def test_multiple_events(self, db_):
        v = Vehicle(plate_no='TRK-TRK2', vehicle_type='van',
                    load_capacity=1000.0, volume_capacity=10.0)
        db_.session.add(v); db_.session.commit()
        d = Driver(name='追踪司2', phone='13800000011', license_no='LT2', license_type='B',
                   license_expire_date=date(2030, 12, 31))
        db_.session.add(d); db_.session.commit()
        s = Shipment(vehicle_id=v.id, driver_id=d.id)
        db_.session.add(s); db_.session.commit()
        TrackingService.record_event(s.id, 'departed', '上海')
        TrackingService.record_event(s.id, 'arrived', '北京')
        events = TrackingService.get_shipment_route(s.id)
        assert len(events) == 2


# ---------------------------------------------------------------------------
# TrackingService.add_exception
# ---------------------------------------------------------------------------
class TestTrackingAddException:
    def test_valid_damage_type(self, db_):
        v = Vehicle(plate_no='TRK-TRK3', vehicle_type='van',
                    load_capacity=1000.0, volume_capacity=10.0)
        db_.session.add(v); db_.session.commit()
        d = Driver(name='异常司', phone='13800000012', license_no='LT3', license_type='B',
                   license_expire_date=date(2030, 12, 31))
        db_.session.add(d); db_.session.commit()
        s = Shipment(vehicle_id=v.id, driver_id=d.id)
        db_.session.add(s); db_.session.commit()
        result = TrackingService.add_exception(s.id, 'damage', '货物损坏')
        assert result['exception_type'] == 'damage'

    def test_valid_loss_type(self, db_):
        v = Vehicle(plate_no='TRK-TRK4', vehicle_type='van',
                    load_capacity=1000.0, volume_capacity=10.0)
        db_.session.add(v); db_.session.commit()
        d = Driver(name='异常司4', phone='13800000013', license_no='LT4', license_type='B',
                   license_expire_date=date(2030, 12, 31))
        db_.session.add(d); db_.session.commit()
        s = Shipment(vehicle_id=v.id, driver_id=d.id)
        db_.session.add(s); db_.session.commit()
        result = TrackingService.add_exception(s.id, 'loss', '货物丢失')
        assert result['exception_type'] == 'loss'

    def test_valid_delay_type(self, db_):
        v = Vehicle(plate_no='TRK-TRK5', vehicle_type='van',
                    load_capacity=1000.0, volume_capacity=10.0)
        db_.session.add(v); db_.session.commit()
        d = Driver(name='异常司5', phone='13800000014', license_no='LT5', license_type='B',
                   license_expire_date=date(2030, 12, 31))
        db_.session.add(d); db_.session.commit()
        s = Shipment(vehicle_id=v.id, driver_id=d.id)
        db_.session.add(s); db_.session.commit()
        result = TrackingService.add_exception(s.id, 'delay', '交通延误')
        assert result['exception_type'] == 'delay'

    def test_valid_refused_type(self, db_):
        v = Vehicle(plate_no='TRK-TRK6', vehicle_type='van',
                    load_capacity=1000.0, volume_capacity=10.0)
        db_.session.add(v); db_.session.commit()
        d = Driver(name='异常司6', phone='13800000015', license_no='LT6', license_type='B',
                   license_expire_date=date(2030, 12, 31))
        db_.session.add(d); db_.session.commit()
        s = Shipment(vehicle_id=v.id, driver_id=d.id)
        db_.session.add(s); db_.session.commit()
        result = TrackingService.add_exception(s.id, 'refused', '客户拒收')
        assert result['exception_type'] == 'refused'

    def test_invalid_type_raises(self, db_):
        v = Vehicle(plate_no='TRK-TRK7', vehicle_type='van',
                    load_capacity=1000.0, volume_capacity=10.0)
        db_.session.add(v); db_.session.commit()
        d = Driver(name='异常司7', phone='13800000016', license_no='LT7', license_type='B',
                   license_expire_date=date(2030, 12, 31))
        db_.session.add(d); db_.session.commit()
        s = Shipment(vehicle_id=v.id, driver_id=d.id)
        db_.session.add(s); db_.session.commit()
        with pytest.raises(ValueError):
            TrackingService.add_exception(s.id, 'invalid_type', 'some description')
