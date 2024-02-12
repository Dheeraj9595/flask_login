from flask import Flask, render_template, request, jsonify
from flask_bcrypt import Bcrypt  # Make sure to install flask-bcrypt
from db import SessionLocal, User
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
# from users import users_bp


app = Flask(__name__)
bcrypt = Bcrypt(app)
db: Session = SessionLocal()

# Your existing routes go here...


# Render todo form
@app.route('/todo/', methods=['GET'])
def render_todo():
    return render_template('index.html')


###users apis 



# Render registration form
@app.route('/register/', methods=['GET'])
def render_register():
    return render_template('register.html')

# Render login form
@app.route('/login/', methods=['GET'])
def render_login():
    return render_template('login.html')

# # Handle registration form submission
# @users_bp.route('/register/', methods=['POST'])
# def register_user():
#     username = request.form.get('username')
#     password = request.form.get('password')
#     first_name = request.form.get('first_name')
#     last_name = request.form.get('last_name')
#     email = request.form.get('email')

#     hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

#     try:
#         new_user = User(username=username, password=hashed_password, first_name=first_name, last_name=last_name, email=email)
#         db.add(new_user)
#         db.commit()
#         return jsonify({"message": "User registered successfully"})
#     except IntegrityError:
#         db.rollback()
#         return jsonify({"error": "Username already exists"}), 400
#     finally:
#         db.close()

@app.route('/register/', methods=['POST'])
def register_user():
    if request.is_json:
        # Handling JSON data
        user_data = request.json
        username = user_data.get('username')
        password = user_data.get('password')
        first_name = user_data.get('first_name')
        last_name = user_data.get('last_name')
        email = user_data.get('email')
    else:
        # Handling form data
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        new_user = User(username=username, password=hashed_password, first_name=first_name, last_name=last_name, email=email)
        db.add(new_user)
        db.commit()
        return jsonify({"message": "User registered successfully"}), 200, {'Content-Type': 'application/json'}
    except IntegrityError:
        db.rollback()
        return jsonify({"error": "Username already exists"}), 400
    finally:
        db.close()




# Handle login form submission
@app.route('/login/', methods=['POST'])
def login_user():
    username = request.form.get('username')
    password = request.form.get('password')

    user = db.query(User).filter_by(username=username).first()

    if user and bcrypt.check_password_hash(user.password, password):
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"error": "Invalid username or password"}), 401

def user_serializer(user):
    return {"username": user.username, "email": user.email, "name": user.first_name + user.last_name}

@app.route('/show-user/<user_id>/', methods=['GET'])
def show_user_by_id(user_id):
    users = db.query(User).filter(User.id == user_id).first()
    serializer = [user_serializer(users)]
    return serializer

@app.route('/update-user/<user_id>/', methods=['PATCH'])
def update_user(user_id:int):
    update_user_data = request.json
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        for key,value in update_user_data.items():
            setattr(user, key, value)
        db.commit()
        return jsonify({"message": f"User with ID {user_id} updated successfully"})
    else:
        return jsonify({"message": f"User with ID {user_id} not found"})    








# app.register_blueprint(users_bp, url_prefix='/api/users')

if __name__ == "__main__":
    app.run(debug=True)
