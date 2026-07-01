"""
Route Service - Route management, distance calculation, waypoint optimization.
Uses SQLAlchemy models from backend.models.
"""
import math
import random
import json
from datetime import datetime
from typing import Optional, List

from backend.extensions import db
from backend.models.route import Route
from backend.models.shipment import Shipment


# Vehicle speed in km/h
VEHICLE_SPEEDS = {
    'van': 60, 'mini_van': 50, 'truck': 50, 'large_truck': 45,
}


class RouteService:
    """Service for managing delivery routes."""

    EARTH_RADIUS_KM = 6371.0

    @staticmethod
    def generate_route_no() -> str:
        """Generate 'RT' + YYYYMMDD + 4 random digits."""
        ts = datetime.now().strftime('%Y%m%d')
        suffix = ''.join(random.choices('0123456789', k=4))
        return f'RT{ts}{suffix}'

    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km between two lat/lng points."""
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return RouteService.EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))

    @classmethod
    def calculate_distance(cls, origin: dict, destination: dict,
                           waypoints: Optional[List[dict]] = None) -> float:
        """Total distance in km: Haversine + 30% road factor."""
        waypoints = waypoints or []
        total = 0.0
        points = [origin] + waypoints + [destination]
        for i in range(len(points) - 1):
            total += cls.haversine(
                points[i].get('lat', 0), points[i].get('lng', 0),
                points[i + 1].get('lat', 0), points[i + 1].get('lng', 0),
            )
        return round(total * 1.3, 2)

    @classmethod
    def estimate_delivery_time(cls, distance: float, vehicle_type: str = 'van') -> int:
        """Estimated time in minutes based on distance and vehicle speed."""
        speed = VEHICLE_SPEEDS.get(vehicle_type, 60)
        return int(round(distance / speed * 60))

    @classmethod
    def optimize_waypoints(cls, waypoints: List[dict]) -> List[dict]:
        """Nearest-neighbor TSP approximation for waypoint ordering."""
        if not waypoints:
            return []
        if len(waypoints) == 1:
            return list(waypoints)

        remaining = list(waypoints)
        ordered = [remaining.pop(0)]
        while remaining:
            current = ordered[-1]
            nearest_idx = min(
                range(len(remaining)),
                key=lambda i: cls.haversine(
                    current.get('lat', 0), current.get('lng', 0),
                    remaining[i].get('lat', 0), remaining[i].get('lng', 0),
                )
            )
            ordered.append(remaining.pop(nearest_idx))
        return ordered

    @classmethod
    def create_route(cls, data: dict) -> Route:
        """Create a route with auto-calculated distance and time."""
        origin = data.get('origin', {})
        destination = data.get('destination', {})
        waypoints = data.get('waypoints', [])
        vehicle_type = data.get('vehicle_type', 'van')

        optimized = cls.optimize_waypoints(waypoints)
        distance = cls.calculate_distance(origin, destination, optimized)
        estimated_time = cls.estimate_delivery_time(distance, vehicle_type)

        route = Route(
            route_no=cls.generate_route_no(),
            origin_city=origin.get('city', ''),
            origin_province=origin.get('province', ''),
            destination_city=destination.get('city', ''),
            destination_province=destination.get('province', ''),
            distance=distance,
            estimated_time=estimated_time,
            waypoints=json.dumps(waypoints),
            status='planned',
        )
        db.session.add(route)
        db.session.commit()
        return route

    @staticmethod
    def assign_route_to_shipment(route_id: str, shipment_id: str) -> Route:
        """Assign a route to a shipment."""
        route = db.session.get(Route, route_id)
        if not route:
            raise KeyError(f'Route not found: {route_id}')
        if route.status not in ('planned', 'in_progress'):
            raise ValueError(f"Cannot assign: route is '{route.status}'")
        route.route_id = route_id  # Shipment.route_id
        shipment = db.session.get(Shipment, shipment_id)
        if shipment:
            shipment.route_id = route_id
        route.status = 'in_progress'
        db.session.commit()
        return route

    @staticmethod
    def get_active_routes() -> list:
        """Return all planned or in-progress routes."""
        return Route.query.filter(
            Route.status.in_(['planned', 'in_progress'])
        ).all()

    @staticmethod
    def complete_route(route_id: str) -> Route:
        """Mark route as completed."""
        route = db.session.get(Route, route_id)
        if not route:
            raise KeyError(f'Route not found: {route_id}')
        route.status = 'completed'
        db.session.commit()
        return route
