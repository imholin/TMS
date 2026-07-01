from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.api import api_bp
from backend.extensions import db
from backend.models import Driver
from backend.services.shipment_service import ShipmentService

@api_bp.route('/drivers', methods=['GET'])
@jwt_required()
def list_drivers():
    status = request.args.get('status')
    query = Driver.query
    if status:
        query = query.filter_by(status=status)
    drivers = query.all()
    return {'code': 200, 'message': 'success', 'data': [d.to_dict() for d in drivers]}, 200

@api_bp.route('/drivers', methods=['POST'])
@jwt_required()
def create_driver():
    data = request.get_json() or {}
    required = ['name', 'phone']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return {'code': 400, 'message': f'Missing: {missing}'}, 400
    d = Driver(
        name=data['name'], phone=data['phone'],
        id_card_no=data.get('id_card_no'), license_no=data.get('license_no'),
        license_type=data.get('license_type', 'B'),
        license_expire_date=data.get('license_expire_date'),
        status=data.get('status', 'active'),
        hire_date=data.get('hire_date'),
        salary_type=data.get('salary_type', 'monthly'),
        base_salary=float(data.get('base_salary', 8000)),
    )
    db.session.add(d)
    db.session.commit()
    return {'code': 201, 'message': 'Driver created', 'data': d.to_dict()}, 201

@api_bp.route('/drivers/<driver_id>', methods=['GET'])
@jwt_required()
def get_driver(driver_id):
    d = db.session.get(Driver, driver_id)
    if not d:
        return {'code': 404, 'message': 'Driver not found'}, 404
    return {'code': 200, 'message': 'success', 'data': d.to_dict()}, 200

@api_bp.route('/drivers/<driver_id>', methods=['PUT'])
@jwt_required()
def update_driver(driver_id):
    d = db.session.get(Driver, driver_id)
    if not d:
        return {'code': 404, 'message': 'Driver not found'}, 404
    data = request.get_json() or {}
    for field in ['name', 'phone', 'id_card_no', 'license_no', 'license_type',
                  'license_expire_date', 'salary_type', 'base_salary']:
        if field in data:
            setattr(d, field, data[field])
    db.session.commit()
    return {'code': 200, 'message': 'Driver updated', 'data': d.to_dict()}, 200

@api_bp.route('/drivers/<driver_id>/status', methods=['PUT'])
@jwt_required()
def update_driver_status(driver_id):
    d = db.session.get(Driver, driver_id)
    if not d:
        return {'code': 404, 'message': 'Driver not found'}, 404
    new_status = request.args.get('status') or (request.get_json() or {}).get('status')
    if new_status not in ('active', 'on_duty', 'on_leave', 'suspended'):
        return {'code': 400, 'message': 'Invalid status'}, 400
    d.status = new_status
    db.session.commit()
    return {'code': 200, 'message': f'Driver status -> {new_status}', 'data': d.to_dict()}, 200

@api_bp.route('/drivers/<driver_id>/shipments', methods=['GET'])
@jwt_required()
def driver_shipments(driver_id):
    d = db.session.get(Driver, driver_id)
    if not d:
        return {'code': 404, 'message': 'Driver not found'}, 404
    shipments = ShipmentService.get_shipments_by_driver(driver_id)
    return {'code': 200, 'message': 'success', 'data': [s.to_dict() for s in shipments]}, 200