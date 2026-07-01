from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# Import models from the models/ package to register them with SQLAlchemy.
# Must be after db initialization to avoid circular imports.
def init_models():
    # Import submodules first so BaseModel is available
    from backend.models.base     import BaseModel
    from backend.models.user     import User
    from backend.models.order    import Order
    from backend.models.vehicle  import Vehicle
    from backend.models.driver   import Driver
    from backend.models.route    import Route
    from backend.models.expense  import Expense
    from backend.models.shipment  import Shipment, ShipmentOrder
    return User, Order, Vehicle, Driver, Route, Expense, Shipment, ShipmentOrder
