from flask import Flask, render_template, request, jsonify
from flask_bcrypt import Bcrypt  # Make sure to install flask-bcrypt
from db import SessionLocal, User
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

app = Flask(__name__)
bcrypt = Bcrypt(app)
db: Session = SessionLocal()

# Your existing routes go here...

# Render registration form
@app.route('/register/', methods=['GET'])
def render_register():
    return render_template('register.html')

# Render login form
@app.route('/login/', methods=['GET'])
def render_login():
    return render_template('login.html')

# Handle registration form submission
@app.route('/register/', methods=['POST'])
def register_user():
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
        return jsonify({"message": "User registered successfully"})
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

if __name__ == "__main__":
    app.run(debug=True)
