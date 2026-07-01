"""
TMS CLI - Command Line Interface for Express Delivery TMS.
Usage: python backend/cli.py <command> [options]
"""
import os
import sys
import click
import json
from datetime import datetime, date

# Add backend to path
_backend_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_backend_dir)
sys.path.insert(0, _root_dir)

os.environ.setdefault('FLASK_ENV', 'development')


@click.group()
def cli():
    """TMS Command Line Interface - Express Delivery Management"""
    pass


# ── Database commands ──────────────────────────────────────────────

@cli.group()
def db():
    """Database management"""
    pass


@db.command('init')
def db_init():
    """Initialize database and create tables"""
    from backend.extensions import db
    from backend.app import create_app
    app = create_app('development')
    with app.app_context():
        db.create_all()
        click.echo('[OK] Database initialized')


@db.command('reset')
def db_reset():
    """Drop all tables and re-initialize (WARNING: destroys all data)"""
    app = create_app('development')
    with app.app_context():
        db.drop_all()
        db.create_all()
        click.echo('[OK] Database reset - all tables dropped and recreated')


@db.command('seed')
def db_seed():
    """Seed demo data (vehicles, drivers, sample orders)"""
    from backend.extensions import db
    from backend.models import User, Vehicle, Driver, Order
    from backend.app import create_app
    from datetime import date
    import random

    app = create_app('development')
    with app.app_context():
        if Vehicle.query.first():
            click.echo('[--] Already seeded')
            return

        cities = [
            ('Shanghai', 'Shanghai'), ('Beijing', 'Beijing'), ('Guangzhou', 'Guangdong'),
            ('Shenzhen', 'Guangdong'), ('Hangzhou', 'Zhejiang'), ('Nanjing', 'Jiangsu'),
            ('Chengdu', 'Sichuan'), ('Wuhan', 'Hubei'),
        ]
        vehicle_data = [
            ('SH0001', 'van', 'Ford', 'Transit', 2000, 12.0),
            ('SH0002', 'van', 'Ford', 'Transit', 2000, 12.0),
            ('BJ0001', 'truck', 'Dongfeng', 'EQ1090', 5000, 25.0),
            ('GZ0001', 'large_truck', 'Sinotruk', 'HOWO', 10000, 50.0),
            ('SZ0001', 'mini_van', 'JAC', 'Refine', 1000, 6.0),
            ('HZ0001', 'van', 'FAW', 'J6F', 2000, 12.0),
            ('NJ0001', 'truck', 'Dongfeng', 'T5G', 5000, 25.0),
            ('CD0001', 'van', 'Changan', 'Star', 2000, 12.0),
        ]
        drivers = [
            ('Zhang Wei', '13800001001'), ('Li Hua', '13800001002'),
            ('Wang Qiang', '13800001003'), ('Liu Yang', '13800001004'),
            ('Chen Min', '13800001005'), ('Zhao Long', '13800001006'),
            ('Sun Kai', '13800001007'), ('Zhou Tao', '13800001008'),
        ]

        vehicles = []
        for plate, vtype, brand, model, load, vol in vehicle_data:
            v = Vehicle(
                plate_no=plate, vehicle_type=vtype, brand=brand, model=model,
                load_capacity=load, volume_capacity=vol, status='available',
                fuel_type='diesel', fuel_consumption=10.0, mileage=50000
            )
            db.session.add(v)
            vehicles.append(v)

        drivers_out = []
        for name, phone in drivers:
            d = Driver(
                name=name, phone=phone,
                id_card_no=f'310101199001{random.randint(100000, 999999)}X',
                license_no=f'31{random.randint(100000, 999999)}',
                license_type='B', license_expire_date=date(2027, 12, 31),
                status='active', hire_date=date(2023, 1, 1),
                salary_type='monthly', base_salary=8000.0
            )
            db.session.add(d)
            drivers_out.append(d)

        db.session.commit()

        # Resolve system user (create if missing)
        user = User.query.filter_by(username='system').first()
        if not user:
            user = User.query.filter_by(username='admin').first()
        if not user:
            user = User.query.first()
        if not user:
            user = User(username='system', password='system123',
                        email='system@tms.local', role='operator')
            db.session.add(user)
            db.session.commit()

        for i in range(20):
            orig, dest = random.sample(cities, 2)
            ts = datetime.now().strftime('%Y%m%d%H%M%S')
            order_no = f'ORD{ts}{i:04d}'
            o = Order(
                order_no=order_no,
                sender_name=f'Sender {i+1}', sender_phone=f'138{random.randint(10000000, 99999999)}',
                sender_address=f'Address {i}A, {orig[0]}', sender_city=orig[0], sender_province=orig[1],
                receiver_name=f'Receiver {i+1}', receiver_phone=f'139{random.randint(10000000, 99999999)}',
                receiver_address=f'Address {i}B, {dest[0]}', receiver_city=dest[0], receiver_province=dest[1],
                weight=round(random.uniform(0.5, 80.0), 2),
                volume=round(random.uniform(100, 5000), 2),
                description=f'Package {i+1}',
                status=random.choice(['pending', 'confirmed', 'confirmed', 'in_transit']),
                payment_type=random.choice(['prepaid', 'cod']),
                cod_amount=round(random.uniform(0, 500), 2),
                total_fee=round(random.uniform(20, 600), 2),
                user_id=user.id,
            )
            db.session.add(o)

        db.session.commit()
        click.echo(f'[OK] Seeded: {len(vehicles)} vehicles, {len(drivers_out)} drivers, 20 orders')


# ── User commands ──────────────────────────────────────────────────

@cli.group()
def user():
    """User management"""
    pass


@user.command('create')
@click.option('--username', required=True)
@click.option('--password', required=True)
@click.option('--email', default='')
@click.option('--role', default='operator', type=click.Choice(['admin', 'operator', 'driver']))
def user_create(username, password, email, role):
    """Create a new user"""
    from backend.extensions import db
    from backend.models import User
    from backend.app import create_app

    app = create_app('development')
    with app.app_context():
        if User.query.filter_by(username=username).first():
            click.echo(f'[FAIL] Username {username} already exists')
            return
        u = User(username=username, password=password, email=email or None, role=role)
        db.session.add(u)
        db.session.commit()
        click.echo(f'[OK] User created: {username} / {role}')


@user.command('list')
def user_list():
    """List all users"""
    from backend.models import User
    from backend.app import create_app
    app = create_app('development')
    with app.app_context():
        users = User.query.all()
        click.echo(f'{"Username":<16} {"Email":<28} {"Role":<10} {"Active"}')
        click.echo('-' * 65)
        for u in users:
            click.echo(f'{u.username:<16} {(u.email or ""):<28} {u.role:<10} {u.is_active}')


# ── Order commands ────────────────────────────────────────────────

@cli.group()
def order():
    """Order management"""
    pass


@order.command('create')
@click.option('--sender', required=True, help='Sender name')
@click.option('--sender-phone', required=True)
@click.option('--sender-addr', required=True)
@click.option('--sender-city', required=True)
@click.option('--receiver', required=True, help='Receiver name')
@click.option('--receiver-phone', required=True)
@click.option('--receiver-addr', required=True)
@click.option('--receiver-city', required=True)
@click.option('--weight', required=True, type=float)
@click.option('--volume', default=0.0, type=float)
@click.option('--desc', default='')
def order_create(sender, sender_phone, sender_addr, sender_city,
                 receiver, receiver_phone, receiver_addr, receiver_city,
                 weight, volume, desc):
    """Create a new order"""
    from backend.models import User
    from backend.services.order_service import OrderService
    from backend.app import create_app

    app = create_app('development')
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        data = {
            'sender_name': sender, 'sender_phone': sender_phone,
            'sender_address': sender_addr, 'sender_city': sender_city,
            'receiver_name': receiver, 'receiver_phone': receiver_phone,
            'receiver_address': receiver_addr, 'receiver_city': receiver_city,
            'weight': weight, 'volume': volume, 'description': desc,
        }
        order = OrderService.create_order(data, user_id=admin.id)
        click.echo(f'[OK] Order created: {order.order_no}')
        click.echo(f'     Fee: {order.total_fee} | Status: {order.status}')


@order.command('list')
@click.option('--status', help='Filter by status')
@click.option('--city', help='Filter by sender city')
@click.option('--limit', default=20, type=int)
def order_list(status, city, limit):
    """List orders"""
    from backend.services.order_service import OrderService
    from backend.app import create_app

    app = create_app('development')
    with app.app_context():
        filters = {}
        if status:
            filters['status'] = status
        if city:
            filters['sender_city'] = city
        items, total = OrderService.get_orders(filters)
        click.echo(f'Total: {total} orders (showing {min(limit, len(items))})')
        click.echo(f'{"Order No":<24} {"Status":<12} {"From":<12} {"To":<12} {"Weight":>8} {"Fee":>8}')
        click.echo('-' * 80)
        for o in items[:limit]:
            click.echo(f'{o.order_no:<24} {o.status:<12} {o.sender_city:<12} {o.receiver_city:<12} {o.weight:>8.1f} {o.total_fee:>8.2f}')


@order.command('status')
@click.argument('order_id')
@click.option('--new-status', help='New status')
def order_status(order_id, new_status):
    """Get or update order status"""
    from backend.services.order_service import OrderService
    from backend.app import create_app

    app = create_app('development')
    with app.app_context():
        try:
            order = OrderService.get_order(order_id)
        except KeyError:
            # Try by order_no
            from backend.models import Order
            order = Order.query.filter_by(order_no=order_id).first()
            if not order:
                click.echo(f'[FAIL] Order not found: {order_id}')
                return

        if new_status:
            try:
                order = OrderService.update_order_status(order.id, new_status)
                click.echo(f'[OK] Order {order.order_no} status -> {new_status}')
            except ValueError as e:
                click.echo(f'[FAIL] {e}')
        else:
            click.echo(f'Order No  : {order.order_no}')
            click.echo(f'Status    : {order.status}')
            click.echo(f'From      : {order.sender_city} -> {order.sender_province}')
            click.echo(f'To        : {order.receiver_city} -> {order.receiver_province}')
            click.echo(f'Weight    : {order.weight} kg')
            click.echo(f'Fee       : {order.total_fee}')


# ── Vehicle commands ───────────────────────────────────────────────

@cli.group()
def vehicle():
    """Vehicle management"""
    pass


@vehicle.command('list')
@click.option('--status', help='Filter by status')
def vehicle_list(status):
    """List all vehicles"""
    from backend.models import Vehicle
    from backend.app import create_app

    app = create_app('development')
    with app.app_context():
        query = Vehicle.query
        if status:
            query = query.filter_by(status=status)
        vehicles = query.all()
        click.echo(f'{"Plate":<10} {"Type":<12} {"Status":<12} {"Load(kg)":>10} {"Fuel":>8} {"Mileage":>10}')
        click.echo('-' * 65)
        for v in vehicles:
            click.echo(f'{v.plate_no:<10} {v.vehicle_type:<12} {v.status:<12} {v.load_capacity:>10.0f} {v.fuel_consumption:>8.1f} {v.mileage:>10.0f}')


@vehicle.command('create')
@click.option('--plate', required=True)
@click.option('--type', 'vtype', default='van', type=click.Choice(['van', 'mini_van', 'truck', 'large_truck']))
@click.option('--brand', default='Unknown')
@click.option('--model', default='Unknown')
@click.option('--load', 'load_cap', default=2000.0, type=float)
@click.option('--volume', 'vol_cap', default=12.0, type=float)
def vehicle_create(plate, vtype, brand, model, load_cap, vol_cap):
    """Create a new vehicle"""
    from backend.extensions import db
    from backend.models import Vehicle
    from backend.app import create_app

    app = create_app('development')
    with app.app_context():
        v = Vehicle(plate_no=plate, vehicle_type=vtype, brand=brand, model=model,
                   load_capacity=load_cap, volume_capacity=vol_cap, status='available',
                   fuel_type='diesel', fuel_consumption=10.0, mileage=0.0)
        db.session.add(v)
        db.session.commit()
        click.echo(f'[OK] Vehicle {plate} created (id: {v.id[:8]})')


# ── Driver commands ───────────────────────────────────────────────

@cli.group()
def driver():
    """Driver management"""
    pass


@driver.command('list')
@click.option('--status', help='Filter by status')
def driver_list(status):
    """List all drivers"""
    from backend.models import Driver
    from backend.app import create_app

    app = create_app('development')
    with app.app_context():
        query = Driver.query
        if status:
            query = query.filter_by(status=status)
        drivers = query.all()
        click.echo(f'{"Name":<14} {"Phone":<14} {"Status":<10} {"Vehicle":<10} {"Salary":>10}')
        click.echo('-' * 62)
        for d in drivers:
            click.echo(f'{d.name:<14} {d.phone:<14} {d.status:<10} {(d.vehicle_id or "-")[:10]:<10} {d.base_salary:>10.0f}')


# ── Expense commands ───────────────────────────────────────────────

@cli.group()
def expense():
    """Expense management"""
    pass


@expense.command('record')
@click.option('--category', required=True, type=click.Choice(['fuel', 'toll', 'driver_salary', 'maintenance', 'food', 'accommodation', 'other']))
@click.option('--amount', required=True, type=float)
@click.option('--desc', default='')
@click.option('--driver-id')
@click.option('--vehicle-id')
def expense_record(category, amount, desc, driver_id, vehicle_id):
    """Record an expense"""
    from backend.extensions import db
    from backend.models import Expense, User
    from backend.app import create_app
    from datetime import datetime as dt

    app = create_app('development')
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        now = dt.now().strftime('%Y%m%d%H%M%S')
        e = Expense(
            expense_no=f'EXP{now}',
            category=category, amount=amount, description=desc,
            driver_id=driver_id, vehicle_id=vehicle_id,
            user_id=admin.id, expense_date=date.today()
        )
        db.session.add(e)
        db.session.commit()
        click.echo(f'[OK] Expense recorded: {category} = {amount}')


# ── Dashboard ────────────────────────────────────────────────────

@cli.command('dashboard')
def dashboard():
    """Show dashboard summary"""
    from backend.models import Order, Vehicle, Driver, Expense
    from backend.extensions import db
    from backend.app import create_app

    app = create_app('development')
    with app.app_context():
        total = Order.query.count()
        pending = Order.query.filter_by(status='pending').count()
        confirmed = Order.query.filter_by(status='confirmed').count()
        in_transit = Order.query.filter_by(status='in_transit').count()
        delivered = Order.query.filter_by(status='delivered').count()
        cancelled = Order.query.filter_by(status='cancelled').count()
        vehicles_total = Vehicle.query.count()
        vehicles_avail = Vehicle.query.filter_by(status='available').count()
        drivers_total = Driver.query.count()
        drivers_active = Driver.query.filter_by(status='active').count()
        today_expenses = db.session.query(db.func.sum(Expense.amount)).filter(
            Expense.expense_date == date.today()
        ).scalar() or 0

        click.echo('')
        click.echo('  ╔═══════════════════════════════════════╗')
        click.echo('  ║     TMS Dashboard  v0.1               ║')
        click.echo('  ╠═══════════════════════════════════════╣')
        click.echo(f'  ║  Orders:                              ║')
        click.echo(f'  ║    Total      : {total:<22}║')
        click.echo(f'  ║    Pending    : {pending:<22}║')
        click.echo(f'  ║    Confirmed  : {confirmed:<22}║')
        click.echo(f'  ║    In Transit : {in_transit:<22}║')
        click.echo(f'  ║    Delivered  : {delivered:<22}║')
        click.echo(f'  ║    Cancelled  : {cancelled:<22}║')
        click.echo(f'  ║  Vehicles    : {vehicles_total:<22}║')
        click.echo(f'  ║    Available  : {vehicles_avail:<22}║')
        click.echo(f'  ║  Drivers      : {drivers_total:<22}║')
        click.echo(f'  ║    Active     : {drivers_active:<22}║')
        click.echo(f'  ║  Today Expense: {today_expenses:<22}║')
        click.echo('  ╚═══════════════════════════════════════╝')
        click.echo('')


# ── Backup / Restore ──────────────────────────────────────────────

@cli.group()
def backup():
    """Database backup/restore"""
    pass


@backup.command('save')
@click.option('--output', default='tms_backup.json', help='Output file path')
def backup_save(output):
    """Export all data to JSON"""
    from backend.models import User, Order, Vehicle, Driver, Route, Expense
    from backend.app import create_app

    app = create_app('development')
    with app.app_context():
        data = {
            'users': [u.to_dict() for u in User.query.all()],
            'orders': [o.to_dict() for o in Order.query.all()],
            'vehicles': [v.to_dict() for v in Vehicle.query.all()],
            'drivers': [d.to_dict() for d in Driver.query.all()],
            'expenses': [e.to_dict() for e in Expense.query.all()],
            'exported_at': datetime.now().isoformat(),
            'version': '0.1',
        }
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        click.echo(f'[OK] Backup saved to {output}')


if __name__ == '__main__':
    cli()
