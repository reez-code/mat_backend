from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from sqlalchemy import MetaData
from sqlalchemy_serializer import SerializerMixin

# Define naming convention for database schema
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)


class Location(db.Model, SerializerMixin):
    __tablename__ = 'locations'
    
    # Serialization rules
    serialize_rules = (
        '-routes_origin.origin',  # Avoid circular reference
        '-routes_destination.destination',  # Avoid circular reference
        '-landmarks.location',  # Avoid circular reference
    )
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    routes_origin = db.relationship("Route", foreign_keys="[Route.origin_id]", back_populates="origin")
    routes_destination = db.relationship("Route", foreign_keys="[Route.destination_id]", back_populates="destination")
    landmarks = db.relationship("Landmark", back_populates="location")

    def __repr__(self):
        return f"<Location {self.name} ({self.latitude}, {self.longitude})>"


class Route(db.Model, SerializerMixin):
    __tablename__ = 'routes'
    
    # Serialization rules
    serialize_rules = (
        '-origin.routes_origin',  # Avoid circular reference
        '-origin.routes_destination',  # Avoid circular reference
        '-destination.routes_origin',  # Avoid circular reference
        '-destination.routes_destination',  # Avoid circular reference
        '-sacco_routes.route',  # Avoid circular reference
    )
    
    id = db.Column(db.Integer, primary_key=True)
    route_number = db.Column(db.String, nullable=True)
    origin_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    destination_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    origin = db.relationship("Location", foreign_keys=[origin_id], back_populates="routes_origin")
    destination = db.relationship("Location", foreign_keys=[destination_id], back_populates="routes_destination")
    sacco_routes = db.relationship("SaccoRoute", back_populates="route")

    def __repr__(self):
        return f"<Route {self.route_number} {self.origin.name} → {self.destination.name}>"


class Sacco(db.Model, SerializerMixin):
    __tablename__ = 'saccos'
    
    # Serialization rules
    serialize_rules = (
        '-sacco_routes.sacco',  # Avoid circular reference
    )
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    matatu_image = db.Column(db.String, nullable=True)

    sacco_routes = db.relationship("SaccoRoute", back_populates="sacco")

    def __repr__(self):
        return f"<Sacco {self.name}>"


class SaccoRoute(db.Model, SerializerMixin):
    __tablename__ = 'sacco_routes'
    
    # Serialization rules
    serialize_rules = (
        '-sacco.sacco_routes',  # Avoid circular reference
        '-route.sacco_routes',  # Avoid circular reference
        '-stops.sacco_route',  # Avoid circular reference
        '-fares.sacco_route',  # Avoid circular reference
    )
    
    id = db.Column(db.Integer, primary_key=True)
    sacco_id = db.Column(db.Integer, db.ForeignKey('saccos.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)

    sacco = db.relationship("Sacco", back_populates="sacco_routes")
    route = db.relationship("Route", back_populates="sacco_routes")
    stops = db.relationship("RouteStop", back_populates="sacco_route")
    fares = db.relationship("Fare", back_populates="sacco_route")

    def __repr__(self):
        return f"<SaccoRoute {self.sacco.name} - {self.route.route_number}>"


class RouteStop(db.Model, SerializerMixin):
    __tablename__ = 'route_stops'
    
    # Serialization rules
    serialize_rules = (
        '-sacco_route.stops',  # Avoid circular reference
        '-location.landmarks',  # Reduce nested data
        '-location.routes_origin',  # Reduce nested data
        '-location.routes_destination',  # Reduce nested data
    )
    
    id = db.Column(db.Integer, primary_key=True)
    sacco_route_id = db.Column(db.Integer, db.ForeignKey('sacco_routes.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    stop_order = db.Column(db.Integer, nullable=False)

    sacco_route = db.relationship("SaccoRoute", back_populates="stops")
    location = db.relationship("Location")

    def __repr__(self):
        return f"<RouteStop {self.location.name} (Order {self.stop_order})>"


class Fare(db.Model, SerializerMixin):
    __tablename__ = 'fares'
    
    # Serialization rules
    serialize_rules = (
        '-sacco_route.fares',  # Avoid circular reference
        '-from_stop.sacco_route',  # Reduce nested data
        '-to_stop.sacco_route',  # Reduce nested data
        '-from_stop.location.landmarks',  # Reduce nested data
        '-from_stop.location.routes_origin',  # Reduce nested data
        '-from_stop.location.routes_destination',  # Reduce nested data
        '-to_stop.location.landmarks',  # Reduce nested data
        '-to_stop.location.routes_origin',  # Reduce nested data
        '-to_stop.location.routes_destination',  # Reduce nested data
    )
    
    id = db.Column(db.Integer, primary_key=True)
    sacco_route_id = db.Column(db.Integer, db.ForeignKey('sacco_routes.id'), nullable=False)
    from_stop_id = db.Column(db.Integer, db.ForeignKey('route_stops.id'), nullable=False)
    to_stop_id = db.Column(db.Integer, db.ForeignKey('route_stops.id'), nullable=False)
    fare_amount = db.Column(db.Integer, nullable=False)
    peak_hours = db.Column(db.Boolean, default=False)

    sacco_route = db.relationship("SaccoRoute", back_populates="fares")
    from_stop = db.relationship("RouteStop", foreign_keys=[from_stop_id])
    to_stop = db.relationship("RouteStop", foreign_keys=[to_stop_id])

    def __repr__(self):
        return f"<Fare {self.fare_amount} from {self.from_stop.location.name} to {self.to_stop.location.name}>"


class Landmark(db.Model, SerializerMixin):
    __tablename__ = 'landmarks'
    
    # Serialization rules
    serialize_rules = (
        '-location.landmarks',  # Avoid circular reference
        '-location.routes_origin',  # Reduce nested data
        '-location.routes_destination',  # Reduce nested data
    )
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    location = db.relationship("Location", back_populates="landmarks")

    def __repr__(self):
        return f"<Landmark {self.name}>"