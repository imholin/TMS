# -*- coding: utf-8 -*-
"""TMS Backend Entry Point.

Run from project root:  python backend/run.py
Or from backend dir:   python run.py
"""
import os
import sys

# Ensure backend/ is on the Python path
_root = os.path.dirname(os.path.abspath(__file__))
_parent = os.path.dirname(_root)
if _parent not in sys.path:
    sys.path.insert(0, _parent)

from backend.app import create_app

config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    print(f'[TMS] Starting server on http://0.0.0.0:5000')
    print(f'[TMS] Health: http://0.0.0.0:5000/health')
    print(f'[TMS] API:    http://0.0.0.0:5000/api/v1/')
    app.run(host='0.0.0.0', port=5000, debug=True)
