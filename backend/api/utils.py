from flask import jsonify, request
from functools import wraps
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from backend.models import User
from backend.extensions import db

def ok(data=None, message='', code=200):
    """Success response helper"""
    response = {'success': True}
    if message:
        response['message'] = message
    if data is not None:
        if isinstance(data, dict):
            response.update(data)
        else:
            response['data'] = data
    return jsonify(response), code

def error(message, code=400, details=None):
    """Error response helper"""
    response = {'success': False, 'error': message}
    if details:
        response['details'] = details
    return jsonify(response), code

def require_role(*roles):
    """Decorator that checks if current user has required role"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                current_user_id = get_jwt_identity()
                current_user = User.query.get(current_user_id)
                
                if not current_user:
                    return error('User not found', 404)
                
                if current_user.role not in roles and current_user.role != 'admin':
                    return error(f'Permission denied. Required roles: {list(roles)}', 403)
                
                return fn(*args, **kwargs)
            except Exception as e:
                return error('Authentication required', 401)
        
        return wrapper
    return decorator

def get_pagination_params():
    """Extract pagination parameters from request args with defaults"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        sort = request.args.get('sort', 'desc')
        
        # Validate
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 1
        if per_page > 100:
            per_page = 100
        
        return {
            'page': page,
            'per_page': per_page,
            'sort': sort
        }
    except Exception:
        return {'page': 1, 'per_page': 20, 'sort': 'desc'}

def paginate(query, page=1, per_page=20):
    """Paginate a SQLAlchemy query and return structured result"""
    try:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return {
            'items': pagination.items,
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    except Exception as e:
        raise ValueError(f'Pagination error: {str(e)}')

def validate_required_fields(data, required_fields):
    """Validate that required fields are present in request data"""
    missing = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing.append(field)
    
    if missing:
        return False, f'Missing required fields: {", ".join(missing)}'
    
    return True, None

def format_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """Format datetime object to string"""
    if dt is None:
        return None
    return dt.strftime(format_str)

def parse_datetime(date_str):
    """Parse datetime string to datetime object"""
    if not date_str:
        return None
    
    # Try different formats
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%d',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f'Unable to parse datetime: {date_str}')

def generate_reference_number(prefix='REF', length=8):
    """Generate a unique reference number"""
    import uuid
    import time
    
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:length].upper()
    
    return f'{prefix}-{datetime.now().strftime("%Y%m%d")}-{unique_id}'

# Example usage in route handlers:
"""
from api.utils import ok, error, require_role, get_pagination_params, paginate

@api_bp.route('/example', methods=['GET'])
@require_role('admin', 'manager')
def example_route():
    try:
        params = get_pagination_params()
        query = ExampleModel.query
        result = paginate(query, params['page'], params['per_page'])
        
        return ok({
            'items': [item.to_dict() for item in result['items']],
            'pagination': {
                'total': result['total'],
                'page': result['page'],
                'per_page': result['per_page'],
                'pages': result['pages']
            }
        })
    except Exception as e:
        return error(str(e))
"""
