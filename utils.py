from functools import wraps
from flask import request, jsonify

def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get API key from headers
        api_key = request.headers.get('x-api-key')
        if not api_key or api_key != 'f50ec0b7-f960-400d-91f0-c42a6d44e3d0':
            return jsonify({"message": "Unauthorized: Invalid or missing API key"}), 401
        return func(*args, **kwargs)
    return wrapper