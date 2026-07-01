# -*- coding: utf-8 -*-
"""Orders API - CRUD + workflow endpoints."""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.api import api_bp
from backend.extensions import db
from backend.models import Order, User
from backend.services.order_service import OrderService
from backend.services.tracking_service import TrackingService


@api_bp.route('/orders', methods=['GET'])
@jwt_required()
def list_orders():
    """List orders with filters and pagination."""
    status = request.args.get('status')
    city = request.args.get('sender_city')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)

    filters = {'page': page, 'per_page': per_page}
    if status:
        filters['status'] = status
    if city:
        filters['sender_city'] = city
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to

    items, total = OrderService.get_orders(filters)
    pages = (total + per_page - 1) // per_page if per_page else 0

    return jsonify({
        'code': 200, 'message': 'success',
        'data': {
            'items': [o.to_dict() for o in items],
            'total': total, 'page': page, 'per_page': per_page, 'pages': pages,
        }
    }), 200


@api_bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    """Create a new delivery order."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    required = ['sender_name', 'sender_phone', 'sender_address', 'sender_city',
                'receiver_name', 'receiver_phone', 'receiver_address', 'receiver_city', 'weight']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'code': 400, 'message': f'Missing fields: {missing}'}), 400

    try:
        order = OrderService.create_order(data, user_id)
        return jsonify({
            'code': 201, 'message': 'Order created',
            'data': order.to_dict(),
        }), 201
    except ValueError as e:
        return jsonify({'code': 400, 'message': str(e)}), 400


@api_bp.route('/orders/<order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """Get a single order by ID."""
    try:
        order = OrderService.get_order(order_id)
        return jsonify({'code': 200, 'message': 'success', 'data': order.to_dict()}), 200
    except KeyError:
        return jsonify({'code': 404, 'message': 'Order not found'}), 404


@api_bp.route('/orders/<order_id>', methods=['PUT'])
@jwt_required()
def update_order(order_id):
    """Update order fields."""
    data = request.get_json() or {}
    try:
        order = OrderService.get_order(order_id)
    except KeyError:
        return jsonify({'code': 404, 'message': 'Order not found'}), 404

    allowed = ['sender_name', 'sender_phone', 'sender_address', 'sender_city',
               'receiver_name', 'receiver_phone', 'receiver_address', 'receiver_city',
               'weight', 'volume', 'description', 'payment_type', 'cod_amount']
    for field in allowed:
        if field in data:
            setattr(order, field, data[field])

    db.session.commit()
    return jsonify({'code': 200, 'message': 'Order updated', 'data': order.to_dict()}), 200


@api_bp.route('/orders/<order_id>/confirm', methods=['POST'])
@jwt_required()
def confirm_order(order_id):
    """Confirm a pending order."""
    try:
        order = OrderService.confirm_order(order_id)
        return jsonify({'code': 200, 'message': 'Order confirmed', 'data': order.to_dict()}), 200
    except ValueError as e:
        return jsonify({'code': 400, 'message': str(e)}), 400


@api_bp.route('/orders/<order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order(order_id):
    """Cancel an order (before in_transit)."""
    try:
        order = OrderService.cancel_order(order_id)
        return jsonify({'code': 200, 'message': 'Order cancelled', 'data': order.to_dict()}), 200
    except ValueError as e:
        return jsonify({'code': 400, 'message': str(e)}), 400


@api_bp.route('/orders/<order_id>/tracking', methods=['GET'])
@jwt_required()
def get_order_tracking(order_id):
    """Get all tracking events for an order's shipments."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'code': 404, 'message': 'Order not found'}), 404

    # Find shipments linked to this order
    from backend.models import ShipmentOrder, Shipment
    links = ShipmentOrder.query.filter_by(order_id=order_id).all()
    shipment_ids = [link.shipment_id for link in links]

    events = []
    for sid in shipment_ids:
        events.extend(TrackingService.get_shipment_route(sid))

    return jsonify({
        'code': 200, 'message': 'success',
        'data': {'order_id': order_id, 'order_no': order.order_no, 'events': events}
    }), 200
