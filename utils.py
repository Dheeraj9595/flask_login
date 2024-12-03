import os
import string
from functools import wraps
import random

from flask import request, jsonify


def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get API key from headers
        api_key = request.headers.get("x-api-key")
        if not api_key or api_key != os.environ.get("api_key"):
            return jsonify({"message": "Unauthorized: Invalid or missing API key"}), 401
        return func(*args, **kwargs)

    return wrapper

# Function to generate the transaction ID
def generate_transaction_id():
    # 'T' followed by 13 random digits
    return 'T' + ''.join(random.choices(string.digits, k=13))