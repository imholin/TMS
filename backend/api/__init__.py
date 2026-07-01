from flask import Blueprint
api_bp = Blueprint('api', __name__)
from . import auth, orders, shipments, vehicles, drivers, routes_api, expenses
from .dashboard import dashboard_bp

# Register dashboard routes under /api/v1/dashboard
api_bp.register_blueprint(dashboard_bp, url_prefix='/dashboard')
