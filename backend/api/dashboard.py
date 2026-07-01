# -*- coding: utf-8 -*-
"""Dashboard API - Statistics and analytics."""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

# Local dashboard blueprint (avoids circular import with api/__init__.py)
dashboard_bp = Blueprint('dashboard', __name__)
from backend.extensions import db
from backend.models import Order, Shipment, Vehicle, Driver, Route, Expense, User
from datetime import datetime, date, timedelta
from sqlalchemy import func


@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    """Key metrics: orders, vehicles, drivers, today's financials."""
    today = date.today()
    month_start = today.replace(day=1)

    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    in_transit_orders = Order.query.filter_by(status='in_transit').count()
    delivered_today = Order.query.filter(
        func.date(Order.updated_at) == today,
        Order.status == 'delivered'
    ).count()
    cancelled_orders = Order.query.filter_by(status='cancelled').count()

    total_vehicles = Vehicle.query.count()
    avail_vehicles = Vehicle.query.filter_by(status='available').count()
    maintenance_vehicles = Vehicle.query.filter_by(status='maintenance').count()

    total_drivers = Driver.query.count()
    active_drivers = Driver.query.filter_by(status='active').count()

    total_shipments = Shipment.query.count()
    active_routes = Route.query.filter(Route.status.in_(['planned', 'in_progress'])).count()

    today_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.expense_date == str(today)
    ).scalar() or 0.0

    today_revenue = db.session.query(func.sum(Order.total_fee)).filter(
        func.date(Order.updated_at) == today,
        Order.status == 'delivered'
    ).scalar() or 0.0

    return {
        'code': 200, 'message': 'success',
        'data': {
            'orders': {
                'total': total_orders, 'pending': pending_orders,
                'in_transit': in_transit_orders, 'delivered_today': delivered_today,
                'cancelled': cancelled_orders,
            },
            'vehicles': {
                'total': total_vehicles, 'available': avail_vehicles,
                'maintenance': maintenance_vehicles,
            },
            'drivers': {'total': total_drivers, 'active': active_drivers},
            'shipments': {'total': total_shipments},
            'routes': {'active': active_routes},
            'today': {
                'revenue': float(today_revenue),
                'expenses': float(today_expenses),
                'profit': float(today_revenue - today_expenses),
            }
        }
    }, 200


@dashboard_bp.route('/dashboard/orders-by-status', methods=['GET'])
@jwt_required()
def orders_by_status():
    """Count of orders grouped by status."""
    results = db.session.query(
        Order.status, func.count(Order.id)
    ).group_by(Order.status).all()
    return {
        'code': 200, 'message': 'success',
        'data': {status: count for status, count in results}
    }, 200


@dashboard_bp.route('/dashboard/revenue-trend', methods=['GET'])
@jwt_required()
def revenue_trend():
    """Daily revenue for the last N days."""
    days = min(int(request.args.get('days', 30)), 90)
    today = date.today()
    start = today - timedelta(days=days - 1)
    results = db.session.query(
        func.date(Order.updated_at).label('date'),
        func.sum(Order.total_fee)
    ).filter(
        Order.status == 'delivered',
        func.date(Order.updated_at) >= start
    ).group_by(func.date(Order.updated_at)).all()
    return {
        'code': 200, 'message': 'success',
        'data': [{'date': str(r.date), 'revenue': float(r[1] or 0)} for r in results]
    }, 200


@dashboard_bp.route('/dashboard/top-routes', methods=['GET'])
@jwt_required()
def top_routes():
    """Top routes by shipment count."""
    limit = min(int(request.args.get('limit', 10)), 50)
    results = db.session.query(
        Route.origin_city, Route.destination_city,
        func.count(Shipment.id).label('shipment_count'),
        func.sum(Route.distance).label('total_distance')
    ).join(Shipment, Shipment.route_id == Route.id
    ).group_by(Route.origin_city, Route.destination_city
    ).order_by(func.count(Shipment.id).desc()
    ).limit(limit).all()
    return {
        'code': 200, 'message': 'success',
        'data': [{
            'from': r[0], 'to': r[1],
            'shipment_count': r[2], 'total_distance': float(r[3] or 0)
        } for r in results]
    }, 200


@dashboard_bp.route('/dashboard/vehicle-utilization', methods=['GET'])
@jwt_required()
def vehicle_utilization():
    """Vehicle usage statistics."""
    total = Vehicle.query.count()
    if total == 0:
        return {'code': 200, 'message': 'success', 'data': {'utilization_rate': 0, 'total': 0, 'in_use': 0}}, 200
    in_use = Vehicle.query.filter_by(status='on_delivery').count()
    return {
        'code': 200, 'message': 'success',
        'data': {
            'total': total, 'in_use': in_use,
            'available': total - in_use,
            'utilization_rate': round(in_use / total * 100, 2),
        }
    }, 200


@dashboard_bp.route('/dashboard/expense-trend', methods=['GET'])
@jwt_required()
def expense_trend():
    """Daily expenses for the last N days."""
    days = min(int(request.args.get('days', 30)), 90)
    today = date.today()
    start = today - timedelta(days=days - 1)
    results = db.session.query(
        Expense.expense_date, func.sum(Expense.amount)
    ).filter(
        Expense.expense_date >= str(start)
    ).group_by(Expense.expense_date).all()
    return {
        'code': 200, 'message': 'success',
        'data': [{'date': str(r.expense_date), 'amount': float(r[1] or 0)} for r in results]
    }, 200
