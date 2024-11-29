import os
from functools import wraps
from flask import request, jsonify

def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get API key from headers
        api_key = request.headers.get('x-api-key')
        if not api_key or api_key != os.environ.get('api_key'):
            return jsonify({"message": "Unauthorized: Invalid or missing API key"}), 401
        return func(*args, **kwargs)
    return wrapper