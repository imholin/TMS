from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from backend.api import api_bp
from backend.extensions import db
from backend.models import Vehicle
from backend.services.shipment_service import ShipmentService

@api_bp.route("/vehicles", methods=["GET"])
@jwt_required()
def list_vehicles():
    status = request.args.get("status")
    vtype = request.args.get("type")
    query = Vehicle.query
    if status:
        query = query.filter_by(status=status)
    if vtype:
        query = query.filter_by(vehicle_type=vtype)
    vehicles = query.all()
    return {"code": 200, "message": "success", "data": [v.to_dict() for v in vehicles]}, 200

@api_bp.route("/vehicles", methods=["POST"])
@jwt_required()
def create_vehicle():
    data = request.get_json() or {}
    required = ["plate_no", "vehicle_type"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return {"code": 400, "message": f"Missing: {missing}"}, 400
    v = Vehicle(
        plate_no=data["plate_no"],
        vehicle_type=data["vehicle_type"],
        brand=data.get("brand", ""),
        model=data.get("model", ""),
        load_capacity=float(data.get("load_capacity", 2000)),
        volume_capacity=float(data.get("volume_capacity", 12)),
        status="available",
        fuel_type=data.get("fuel_type", "diesel"),
        fuel_consumption=float(data.get("fuel_consumption", 10)),
        mileage=float(data.get("mileage", 0)),
    )
    db.session.add(v)
    db.session.commit()
    return {"code": 201, "message": "Vehicle created", "data": v.to_dict()}, 201

@api_bp.route("/vehicles/<vehicle_id>", methods=["GET"])
@jwt_required()
def get_vehicle(vehicle_id):
    v = db.session.get(Vehicle, vehicle_id)
    if not v:
        return {"code": 404, "message": "Vehicle not found"}, 404
    return {"code": 200, "message": "success", "data": v.to_dict()}, 200

@api_bp.route("/vehicles/<vehicle_id>", methods=["PUT"])
@jwt_required()
def update_vehicle(vehicle_id):
    v = db.session.get(Vehicle, vehicle_id)
    if not v:
        return {"code": 404, "message": "Vehicle not found"}, 404
    data = request.get_json() or {}
    for field in ["brand", "model", "load_capacity", "volume_capacity",
                   "fuel_type", "fuel_consumption", "mileage"]:
        if field in data:
            setattr(v, field, data[field])
    db.session.commit()
    return {"code": 200, "message": "Vehicle updated", "data": v.to_dict()}, 200

@api_bp.route("/vehicles/<vehicle_id>/status", methods=["PUT"])
@jwt_required()
def update_vehicle_status(vehicle_id):
    v = db.session.get(Vehicle, vehicle_id)
    if not v:
        return {"code": 404, "message": "Vehicle not found"}, 404
    new_status = request.args.get("status") or (request.get_json() or {}).get("status")
    if new_status not in ("available", "on_delivery", "maintenance", "retired"):
        return {"code": 400, "message": "Invalid status"}, 400
    v.status = new_status
    db.session.commit()
    return {"code": 200, "message": f"Status -> {new_status}", "data": v.to_dict()}, 200

@api_bp.route("/vehicles/<vehicle_id>/shipments", methods=["GET"])
@jwt_required()
def vehicle_shipments(vehicle_id):
    shipments = ShipmentService.get_shipments_by_vehicle(vehicle_id)
    return {"code": 200, "message": "success", "data": [s.to_dict() for s in shipments]}, 200

@api_bp.route("/vehicles/<vehicle_id>", methods=["DELETE"])
@jwt_required()
def delete_vehicle(vehicle_id):
    v = db.session.get(Vehicle, vehicle_id)
    if not v:
        return {"code": 404, "message": "Vehicle not found"}, 404
    v.status = "retired"
    db.session.commit()
    return {"code": 200, "message": "Vehicle retired"}, 200