"""
Tracking Service - Shipment tracking and event management.
Uses SQLAlchemy models from backend.models.
"""
from datetime import datetime
from typing import Optional

from backend.extensions import db
from backend.models.tracking import TrackingEvent, ShipmentException
from backend.models.shipment import Shipment


class TrackingService:
    """Service for recording and querying shipment tracking events."""

    @staticmethod
    def record_event(shipment_id: str, event_type: str, location: str = '',
                     description: str = '', operator: str = '') -> dict:
        """Record a tracking event for a shipment."""
        event = TrackingEvent(
            shipment_id=shipment_id,
            event_type=event_type,
            location=location,
            description=description,
            operator=operator,
            event_time=datetime.now(),
        )
        db.session.add(event)
        db.session.commit()
        return event.to_dict()

    @staticmethod
    def get_shipment_route(shipment_id: str) -> list:
        """Return full tracking history for a shipment, ordered chronologically."""
        events = TrackingEvent.query.filter_by(
            shipment_id=shipment_id
        ).order_by(TrackingEvent.event_time.asc()).all()
        return [e.to_dict() for e in events]

    @staticmethod
    def get_current_location(shipment_id: str) -> Optional[dict]:
        """Return the most recent tracking event (current location)."""
        latest = TrackingEvent.query.filter_by(
            shipment_id=shipment_id
        ).order_by(TrackingEvent.event_time.desc()).first()
        return latest.to_dict() if latest else None

    @staticmethod
    def add_exception(shipment_id: str, exception_type: str,
                      description: str = '', order_id: str = None) -> dict:
        """Record an exception (damage/loss/delay/refused) for a shipment."""
        if exception_type not in ShipmentException.EXCEPTION_TYPES:
            raise ValueError(f"Invalid exception_type: {exception_type}")
        exc = ShipmentException(
            shipment_id=shipment_id,
            exception_type=exception_type,
            description=description,
            order_id=order_id,
            resolved='no',
        )
        db.session.add(exc)
        db.session.commit()
        return exc.to_dict()

    @staticmethod
    def get_exceptions(shipment_id: str) -> list:
        """Return all exceptions for a shipment."""
        excs = ShipmentException.query.filter_by(
            shipment_id=shipment_id
        ).order_by(ShipmentException.created_at.desc()).all()
        return [e.to_dict() for e in excs]

    @staticmethod
    def calculate_eta(shipment_id: str) -> dict:
        """Estimate time to remaining stops based on current progress."""
        shipment = Shipment.query.get(shipment_id)
        if not shipment:
            raise KeyError(f"Shipment not found: {shipment_id}")

        events = TrackingEvent.query.filter_by(
            shipment_id=shipment_id
        ).order_by(TrackingEvent.event_time.asc()).all()

        remaining = shipment.route.estimated_time if shipment.route else 0
        elapsed = 0
        if events:
            first = events[0].event_time
            last = events[-1].event_time
            elapsed = (last - first).total_seconds() / 60

        eta_mins = max(0, remaining - elapsed)
        return {
            'shipment_id': shipment_id,
            'estimated_total_minutes': remaining,
            'elapsed_minutes': round(elapsed, 1),
            'eta_minutes': round(eta_mins, 1),
            'last_location': events[-1].location if events else None,
            'last_event': events[-1].event_type if events else None,
        }
