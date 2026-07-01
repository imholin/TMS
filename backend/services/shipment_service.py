"""
Shipment Service - Shipment creation, workflow, vehicle/driver assignment.
Uses SQLAlchemy models from backend.models.
"""
import random
from datetime import datetime
from typing import Optional

from backend.extensions import db
from backend.models.shipment import Shipment, ShipmentOrder
from backend.models.order import Order
from backend.models.vehicle import Vehicle
from backend.models.driver import Driver
from backend.services.tracking_service import TrackingService


class ShipmentService:
    """Service for managing shipments."""

    @staticmethod
    def generate_shipment_no() -> str:
        """Generate 'SHP' + YYYYMMDD + 4 random digits."""
        ts = datetime.now().strftime('%Y%m%d')
        suffix = ''.join(random.choices('0123456789', k=4))
        return f'SHP{ts}{suffix}'

    @staticmethod
    def create_shipment(data: dict, user_id: str) -> Shipment:
        """Create a shipment, linking orders and optionally assigning vehicle/driver."""
        order_ids = data.get('order_ids', [])
        if not order_ids:
            raise ValueError('At least one order_id is required')

        shipment = Shipment(
            shipment_no=ShipmentService.generate_shipment_no(),
            vehicle_id=data.get('vehicle_id'),
            driver_id=data.get('driver_id'),
            route_id=data.get('route_id'),
            status='prepared',
            notes=data.get('notes', ''),
        )
        db.session.add(shipment)
        db.session.flush()  # Get shipment.id before adding orders

        # Link orders to shipment
        for oid in order_ids:
            link = ShipmentOrder(shipment_id=shipment.id, order_id=oid)
            db.session.add(link)
            # Update order status
            order = db.session.get(Order, oid)
            if order and order.status == 'confirmed':
                order.status = 'picked_up'

        # Assign vehicle
        vehicle_id = data.get('vehicle_id')
        if vehicle_id:
            vehicle = db.session.get(Vehicle, vehicle_id)
            if vehicle and vehicle.status == 'available':
                vehicle.status = 'on_delivery'
                vehicle.current_driver_id = data.get('driver_id')

        db.session.commit()
        return shipment

    @staticmethod
    def assign_vehicle_driver(shipment_id: str, vehicle_id: str, driver_id: str) -> Shipment:
        """Assign vehicle and driver to a shipment."""
        shipment = db.session.get(Shipment, shipment_id)
        if not shipment:
            raise KeyError(f'Shipment not found: {shipment_id}')
        if shipment.status not in ('prepared',):
            raise ValueError(f"Cannot assign: shipment is '{shipment.status}'")

        shipment.vehicle_id = vehicle_id
        shipment.driver_id = driver_id

        vehicle = db.session.get(Vehicle, vehicle_id)
        if vehicle and vehicle.status == 'available':
            vehicle.status = 'on_delivery'
            vehicle.current_driver_id = driver_id

        db.session.commit()
        return shipment

    @staticmethod
    def start_shipment(shipment_id: str) -> Shipment:
        """Set shipment to 'in_transit', record departure event."""
        shipment = db.session.get(Shipment, shipment_id)
        if not shipment:
            raise KeyError(f'Shipment not found: {shipment_id}')
        if shipment.status != 'prepared':
            raise ValueError(f"Cannot start: shipment is '{shipment.status}'")

        shipment.status = 'in_transit'
        shipment.departure_time = datetime.now()
        db.session.commit()

        TrackingService.record_event(
            shipment_id=shipment_id,
            event_type='departed',
            location='Origin hub',
            description='Shipment departed from origin',
            operator='system',
        )
        return shipment

    @staticmethod
    def update_tracking(shipment_id: str, location: str, status: str, notes: str = '') -> dict:
        """Record a tracking event."""
        return TrackingService.record_event(
            shipment_id=shipment_id,
            event_type=status,
            location=location,
            description=notes,
            operator='operator',
        )

    @staticmethod
    def complete_shipment(shipment_id: str, actual_distance: float = None,
                          notes: str = '') -> Shipment:
        """Mark shipment as delivered and release vehicle."""
        shipment = db.session.get(Shipment, shipment_id)
        if not shipment:
            raise KeyError(f'Shipment not found: {shipment_id}')
        if shipment.status != 'in_transit':
            raise ValueError(f"Cannot complete: shipment is '{shipment.status}'")

        shipment.status = 'delivered'
        shipment.arrival_time = datetime.now()
        if actual_distance is not None:
            shipment.actual_distance = actual_distance
        if notes:
            shipment.notes = notes
        db.session.commit()

        # Mark all linked orders as delivered
        for link in shipment.shipment_orders:
            order = link.order
            if order and order.status == 'in_transit':
                order.status = 'delivered'

        # Release vehicle
        vehicle = db.session.get(Vehicle, shipment.vehicle_id)
        if vehicle and vehicle.status == 'on_delivery':
            vehicle.status = 'available'

        db.session.commit()

        TrackingService.record_event(
            shipment_id=shipment_id,
            event_type='delivered',
            location=notes or 'Destination',
            description='Shipment completed',
            operator='system',
        )
        return shipment

    @staticmethod
    def get_shipment_tracking(shipment_id: str) -> list:
        """Return tracking history for a shipment."""
        return TrackingService.get_shipment_route(shipment_id)

    @staticmethod
    def get_shipments_by_vehicle(vehicle_id: str) -> list:
        return Shipment.query.filter_by(vehicle_id=vehicle_id).all()

    @staticmethod
    def get_shipments_by_driver(driver_id: str) -> list:
        return Shipment.query.filter_by(driver_id=driver_id).all()

    @staticmethod
    def get_shipment(shipment_id: str) -> Shipment:
        shipment = db.session.get(Shipment, shipment_id)
        if not shipment:
            raise KeyError(f'Shipment not found: {shipment_id}')
        return shipment
