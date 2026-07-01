from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.api import api_bp
from backend.extensions import db
from backend.models import Route
from backend.services.route_service import RouteService

@api_bp.route("/routes", methods=["GET"])
@jwt_required()
def list_routes():
    routes = RouteService.get_active_routes()
    return {"code": 200, "message": "success", "data": [r.to_dict() for r in routes]}, 200

@api_bp.route("/routes", methods=["POST"])
@jwt_required()
def create_route():
    data = request.get_json() or {}
    required = ["origin", "destination"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return {"code": 400, "message": f"Missing: {missing}"}, 400
    route = RouteService.create_route(data)
    return {"code": 201, "message": "Route created", "data": route.to_dict()}, 201

@api_bp.route("/routes/<route_id>", methods=["GET"])
@jwt_required()
def get_route(route_id):
    r = db.session.get(Route, route_id)
    if not r:
        return {"code": 404, "message": "Route not found"}, 404
    return {"code": 200, "message": "success", "data": r.to_dict()}, 200

@api_bp.route("/routes/<route_id>", methods=["PUT"])
@jwt_required()
def update_route(route_id):
    r = db.session.get(Route, route_id)
    if not r:
        return {"code": 404, "message": "Route not found"}, 404
    data = request.get_json() or {}
    for field in ["origin_city", "destination_city", "distance", "estimated_time"]:
        if field in data:
            setattr(r, field, data[field])
    db.session.commit()
    return {"code": 200, "message": "Route updated", "data": r.to_dict()}, 200

@api_bp.route("/routes/<route_id>/optimize", methods=["POST"])
@jwt_required()
def optimize_route(route_id):
    r = db.session.get(Route, route_id)
    if not r:
        return {"code": 404, "message": "Route not found"}, 404
    import json
    waypoints = json.loads(r.waypoints) if r.waypoints else []
    optimized = RouteService.optimize_waypoints(waypoints)
    return {"code": 200, "message": "Route optimized", "data": {"optimized_waypoints": optimized}}, 200

@api_bp.route("/routes/<route_id>/assign", methods=["POST"])
@jwt_required()
def assign_route(route_id):
    data = request.get_json() or {}
    shipment_id = data.get("shipment_id")
    if not shipment_id:
        return {"code": 400, "message": "shipment_id required"}, 400
    try:
        route = RouteService.assign_route_to_shipment(route_id, shipment_id)
        return {"code": 200, "message": "Route assigned", "data": route.to_dict()}, 200
    except (KeyError, ValueError) as e:
        return {"code": 400, "message": str(e)}, 400

@api_bp.route("/routes/<route_id>/status", methods=["PUT"])
@jwt_required()
def update_route_status(route_id):
    r = db.session.get(Route, route_id)
    if not r:
        return {"code": 404, "message": "Route not found"}, 404
    new_status = request.args.get("status") or (request.get_json() or {}).get("status")
    if new_status in ("planned", "in_progress", "completed", "cancelled"):
        r.status = new_status
        db.session.commit()
        return {"code": 200, "message": f"Status -> {new_status}", "data": r.to_dict()}, 200
    return {"code": 400, "message": "Invalid status"}, 400