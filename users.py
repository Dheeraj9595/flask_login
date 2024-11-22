from typing import Optional

from flask import request, jsonify, Blueprint, render_template, url_for, redirect
from db import User, SessionLocal, create
from flask_bcrypt import bcrypt
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field

db = SessionLocal()

# users_bp = Blueprint('users', __name__, url_prefix='/users')
users_bp = Blueprint('users', __name__, url_prefix='/api/users')


class CreateUser(BaseModel):
    username: str
    password: str
    firstname: Optional[str] = Field(default=None)
    lastname: Optional[str] = Field(default=None)
    email: str


# Render registration form

# Render login form
@users_bp.route('/login/', methods=['GET'])
def render_login():
    return render_template('login.html')


@users_bp.route('/register/', methods=['GET', 'POST'])
def register_user():
    if request.method == "GET":
        return render_template('register.html')
    elif request.method == "POST":
        user_data = request.json
        user = CreateUser(**user_data)

        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

        try:
            # Pass the Pydantic model fields (excluding password) to User constructor
            db_user = User(
                username=user.username,
                email=user.email,
                first_name=user.firstname,
                last_name=user.lastname,
                password=hashed_password
            )

            create(db, db_user)
            serialized_user = {"id": db_user.id, "username": db_user.username}
            return jsonify({"message": "User created successfully", "user": serialized_user})
        except IntegrityError as e:
            db.rollback()
            error_info = e.orig.args
            if "Duplicate entry" in str(error_info):
                return jsonify({"error": "Username already exists"}), 400
            else:
                return jsonify({"error": f"An error occurred while creating the user: {e}"}), 500
        finally:
            db.close()


# Handle login form submission
@users_bp.route('/login/', methods=['POST'])
def login_user():
    # breakpoint()
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    user = db.query(User).filter_by(username=username).first()

    if user and user.password_is_valid(password):
        return redirect(url_for('admin_users'))
    else:
        return jsonify({"error": "Invalid username or password"}), 401


def user_serializer(user):
    return {"username": user.username, "email": user.email, "name": user.first_name + user.last_name}


def user_return_serializer(user):
    return {"id": user.id,"name": user.username, "email": user.email, "created_date": user.created_date}

@users_bp.route('/show-user/<user_id>/', methods=['GET'])
def show_user_by_id(user_id: None):
    if user_id:
        users = db.query(User).filter(User.id == user_id).first()
        if users is None:
            return jsonify({"message": f"No User is found with {user_id} this id"})
        serializer = [user_serializer(users)]
    else:
        all_users = db.query(User).all()
        serializer = [user_serializer(all_users)]
    return serializer


@users_bp.route('/update-user/<user_id>/', methods=['PATCH'])
def update_user(user_id: int):
    update_user_data = request.json
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        for key, value in update_user_data.items():
            setattr(user, key, value)
        db.commit()
        return jsonify({"message": f"User with ID {user_id} updated successfully"})
    else:
        return jsonify({"message": f"User with ID {user_id} not found"})
