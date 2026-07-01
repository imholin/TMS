from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.api import api_bp
from backend.extensions import db
from backend.models import Shipment
from backend.services.shipment_service import ShipmentService
from backend.services.tracking_service import TrackingService

@api_bp.route("/shipments", methods=["GET"])
@jwt_required()
def list_shipments():
    status = request.args.get("status")
    query = Shipment.query
    if status:
        query = query.filter_by(status=status)
    shipments = query.order_by(Shipment.created_at.desc()).limit(100).all()
    return {"code": 200, "message": "success", "data": [s.to_dict() for s in shipments]}, 200

@api_bp.route("/shipments", methods=["POST"])
@jwt_required()
def create_shipment():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    if not data.get("order_ids"):
        return {"code": 400, "message": "order_ids required"}, 400
    try:
        shipment = ShipmentService.create_shipment(data, user_id)
        return {"code": 201, "message": "Shipment created", "data": shipment.to_dict()}, 201
    except ValueError as e:
        return {"code": 400, "message": str(e)}, 400

@api_bp.route("/shipments/<shipment_id>", methods=["GET"])
@jwt_required()
def get_shipment(shipment_id):
    try:
        s = ShipmentService.get_shipment(shipment_id)
        return {"code": 200, "message": "success", "data": s.to_dict()}, 200
    except KeyError:
        return {"code": 404, "message": "Shipment not found"}, 404

@api_bp.route("/shipments/<shipment_id>", methods=["PUT"])
@jwt_required()
def update_shipment(shipment_id):
    s = db.session.get(Shipment, shipment_id)
    if not s:
        return {"code": 404, "message": "Shipment not found"}, 404
    data = request.get_json() or {}
    for field in ["vehicle_id", "driver_id", "route_id", "notes"]:
        if field in data:
            setattr(s, field, data[field])
    db.session.commit()
    return {"code": 200, "message": "Shipment updated", "data": s.to_dict()}, 200

@api_bp.route("/shipments/<shipment_id>/start", methods=["POST"])
@jwt_required()
def start_shipment(shipment_id):
    try:
        s = ShipmentService.start_shipment(shipment_id)
        return {"code": 200, "message": "Shipment in transit", "data": s.to_dict()}, 200
    except (KeyError, ValueError) as e:
        return {"code": 400, "message": str(e)}, 400

@api_bp.route("/shipments/<shipment_id>/complete", methods=["POST"])
@jwt_required()
def complete_shipment(shipment_id):
    data = request.get_json() or {}
    try:
        s = ShipmentService.complete_shipment(
            shipment_id,
            actual_distance=data.get("actual_distance"),
            notes=data.get("notes")
        )
        return {"code": 200, "message": "Shipment delivered", "data": s.to_dict()}, 200
    except (KeyError, ValueError) as e:
        return {"code": 400, "message": str(e)}, 400

@api_bp.route("/shipments/<shipment_id>/tracking", methods=["GET"])
@jwt_required()
def get_shipment_tracking(shipment_id):
    events = TrackingService.get_shipment_route(shipment_id)
    return {"code": 200, "message": "success", "data": events}, 200

@api_bp.route("/shipments/<shipment_id>/tracking", methods=["POST"])
@jwt_required()
def add_tracking_event(shipment_id):
    data = request.get_json() or {}
    if not data.get("event_type"):
        return {"code": 400, "message": "event_type required"}, 400
    event = TrackingService.record_event(
        shipment_id=shipment_id,
        event_type=data["event_type"],
        location=data.get("location", ""),
        description=data.get("description", ""),
        operator=data.get("operator", "operator"),
    )
    return {"code": 201, "message": "Event recorded", "data": event}, 201

@api_bp.route("/shipments/<shipment_id>/assign", methods=["POST"])
@jwt_required()
def assign_shipment(shipment_id):
    data = request.get_json() or {}
    vehicle_id = data.get("vehicle_id")
    driver_id = data.get("driver_id")
    if not vehicle_id or not driver_id:
        return {"code": 400, "message": "vehicle_id and driver_id required"}, 400
    try:
        s = ShipmentService.assign_vehicle_driver(shipment_id, vehicle_id, driver_id)
        return {"code": 200, "message": "Assigned", "data": s.to_dict()}, 200
    except (KeyError, ValueError) as e:
        return {"code": 400, "message": str(e)}, 400

@api_bp.route("/shipments/vehicle/<vehicle_id>", methods=["GET"])
@jwt_required()
def shipments_by_vehicle(vehicle_id):
    shipments = ShipmentService.get_shipments_by_vehicle(vehicle_id)
    return {"code": 200, "message": "success", "data": [s.to_dict() for s in shipments]}, 200

@api_bp.route("/shipments/driver/<driver_id>", methods=["GET"])
@jwt_required()
def shipments_by_driver(driver_id):
    shipments = ShipmentService.get_shipments_by_driver(driver_id)
    return {"code": 200, "message": "success", "data": [s.to_dict() for s in shipments]}, 200