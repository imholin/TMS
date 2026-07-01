from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.api import api_bp
from backend.extensions import db
from backend.models import Expense, User
from backend.services.billing_service import BillingService

@api_bp.route('/expenses', methods=['GET'])
@jwt_required()
def list_expenses():
    category = request.args.get("category")
    driver_id = request.args.get("driver_id")
    vehicle_id = request.args.get("vehicle_id")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    query = Expense.query
    if category:
        query = query.filter_by(category=category)
    if driver_id:
        query = query.filter_by(driver_id=driver_id)
    if vehicle_id:
        query = query.filter_by(vehicle_id=vehicle_id)
    if date_from:
        query = query.filter(Expense.expense_date >= date_from)
    if date_to:
        query = query.filter(Expense.expense_date <= date_to)
    expenses = query.order_by(Expense.expense_date.desc()).all()
    return {"code": 200, "message": "success", "data": [e.to_dict() for e in expenses]}, 200

@api_bp.route("/expenses", methods=["POST"])
@jwt_required()
def create_expense():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    required = ["category", "amount"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return {"code": 400, "message": f"Missing: {missing}"}, 400
    expense = BillingService.record_expense(data, user_id)
    return {"code": 201, "message": "Expense recorded", "data": expense.to_dict()}, 201

@api_bp.route("/expenses/<expense_id>", methods=["GET"])
@jwt_required()
def get_expense(expense_id):
    e = db.session.get(Expense, expense_id)
    if not e:
        return {"code": 404, "message": "Expense not found"}, 404
    return {"code": 200, "message": "success", "data": e.to_dict()}, 200

@api_bp.route("/expenses/<expense_id>", methods=["PUT"])
@jwt_required()
def update_expense(expense_id):
    e = db.session.get(Expense, expense_id)
    if not e:
        return {"code": 404, "message": "Expense not found"}, 404
    data = request.get_json() or {}
    for field in ["category", "amount", "description", "vehicle_id", "driver_id"]:
        if field in data:
            setattr(e, field, data[field])
    db.session.commit()
    return {"code": 200, "message": "Expense updated", "data": e.to_dict()}, 200

@api_bp.route("/expenses/<expense_id>", methods=["DELETE"])
@jwt_required()
def delete_expense(expense_id):
    e = db.session.get(Expense, expense_id)
    if not e:
        return {"code": 404, "message": "Expense not found"}, 404
    db.session.delete(e)
    db.session.commit()
    return {"code": 200, "message": "Expense deleted"}, 200

@api_bp.route("/expenses/summary/daily", methods=["GET"])
@jwt_required()
def daily_summary():
    date_str = request.args.get("date", str(db.func.current_date()))
    result = BillingService.get_daily_summary(date_str)
    return {"code": 200, "message": "success", "data": result}, 200

@api_bp.route("/expenses/summary/monthly", methods=["GET"])
@jwt_required()
def monthly_summary():
    year = int(request.args.get("year", datetime.now().year))
    month = int(request.args.get("month", datetime.now().month))
    result = BillingService.get_monthly_report(year, month)
    return {"code": 200, "message": "success", "data": result}, 200

@api_bp.route("/expenses/shipment/<shipment_id>", methods=["GET"])
@jwt_required()
def expenses_by_shipment(shipment_id):
    result = BillingService.get_expenses_by_shipment(shipment_id)
    return {"code": 200, "message": "success", "data": result}, 200

@api_bp.route("/expenses/driver/<driver_id>", methods=["GET"])
@jwt_required()
def expenses_by_driver(driver_id):
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    result = BillingService.get_expenses_by_driver(driver_id, date_from, date_to)
    return {"code": 200, "message": "success", "data": result}, 200

from datetime import datetime