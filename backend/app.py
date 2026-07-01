# -*- coding: utf-8 -*-
"""TMS Flask Application Factory."""
from flask import Flask
from flask_cors import CORS

from backend.extensions import db, migrate, jwt


def create_app(config_name='default'):
    app = Flask(__name__)

    # Load configuration
    from backend.config import config
    app.config.from_object(config[config_name])

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # JWT token blocklist check (production should use Redis)
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return False  # Allow all tokens until blacklist is implemented

    # Register blueprints
    from backend.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'TMS-API', 'version': '0.1.0'}

    # Create database tables + seed default admin
    with app.app_context():
        # Import ALL models so db.create_all() registers them
        from backend.models import (
            User, Order, Shipment, ShipmentOrder,
            Vehicle, Driver, Route, Expense,
            TrackingEvent, ShipmentException,
        )
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password='admin123',
                email='admin@tms.local',
                role='admin',
            )
            db.session.add(admin)
            db.session.commit()
            print('[TMS] Default admin created: admin / admin123')

    return app
