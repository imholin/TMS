from datetime import datetime
import random
import json

from backend.models.base import BaseModel
from backend.extensions import db


class Route(BaseModel):
    """Route model for delivery routes."""
    __tablename__ = 'routes'
    
    # Route number (format: RT+YYYYMMDD+4 digits)
    route_no = db.Column(db.String(30), unique=True, nullable=False, index=True)
    
    # Origin information
    origin_city = db.Column(db.String(50), nullable=False)
    origin_province = db.Column(db.String(50), nullable=False)
    
    # Destination information
    destination_city = db.Column(db.String(50), nullable=False)
    destination_province = db.Column(db.String(50), nullable=False)
    
    # Route metrics
    distance = db.Column(db.Float, nullable=False)  # km
    estimated_time = db.Column(db.Integer, nullable=False)  # minutes
    
    # Waypoints (JSON list of waypoints with lat/lng/name)
    waypoints = db.Column(db.Text, nullable=True)  # Stored as JSON string
    
    # Status
    status = db.Column(db.String(20), nullable=False, default='planned', index=True)
    
    # Relationships
    shipments = db.relationship('Shipment', back_populates='route', lazy='dynamic')
    
    # Status constants
    STATUS_PLANNED = 'planned'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    
    VALID_STATUSES = [STATUS_PLANNED, STATUS_IN_PROGRESS, STATUS_COMPLETED, STATUS_CANCELLED]
    
    def __init__(self, **kwargs):
        """Initialize Route with auto-generated route_no."""
        super().__init__()
        if 'route_no' not in kwargs:
            kwargs['route_no'] = self._generate_route_no()
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @staticmethod
    def _generate_route_no() -> str:
        """Generate unique route number."""
        now = datetime.now().strftime('%Y%m%d')
        random_digits = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        return f"RT{now}{random_digits}"
    
    @property
    def waypoints_list(self) -> list:
        """Get waypoints as Python list."""
        if self.waypoints:
            try:
                return json.loads(self.waypoints)
            except json.JSONDecodeError:
                return []
        return []
    
    @waypoints_list.setter
    def waypoints_list(self, value: list) -> None:
        """Set waypoints from Python list."""
        self.waypoints = json.dumps(value) if value else None
    
    def add_waypoint(self, latitude: float, longitude: float, name: str = '') -> None:
        """Add a waypoint to the route."""
        waypoints = self.waypoints_list
        waypoints.append({
            'lat': latitude,
            'lng': longitude,
            'name': name
        })
        self.waypoints_list = waypoints
    
    def to_dict(self) -> dict:
        """Convert route to dictionary."""
        result = super().to_dict()
        result.update({
            'route_no': self.route_no,
            'origin_city': self.origin_city,
            'origin_province': self.origin_province,
            'destination_city': self.destination_city,
            'destination_province': self.destination_province,
            'distance': self.distance,
            'estimated_time': self.estimated_time,
            'waypoints': self.waypoints_list,
            'status': self.status
        })
        return result
    
    def __repr__(self) -> str:
        return f"<Route {self.route_no}: {self.origin_city} -> {self.destination_city}>"
