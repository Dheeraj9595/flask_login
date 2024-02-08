# from flask import Flask, request, jsonify
# from db import SessionLocal, User
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError
# from werkzeug.security import generate_password_hash, check_password_hash
# import bcrypt
# from pydantic import BaseModel

# app = Flask(__name__)

# db : Session = SessionLocal()


# @app.route('/', methods=['GET'])
# def root():
#     return {"message": "Working....."}


# class CreateUser(BaseModel):
#     first_name: str
#     last_name: str
#     username: str
#     email: str
#     password: str


# @app.route('/register/', methods=['POST'])
# def register():
#     # Parse JSON data from the request
#     user_data = request.json
#     # Create a Pydantic model instance
#     user = CreateUser(**user_data)
#     # Hash the password using bcrypt
#     hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
#     # Create a new User instance
#     db_user = User(username=user.username, password=hashed_password)
#     # Add the user to the database session
#     db.add(db_user)
    
#     try:
#         # Commit the changes to the database
#         db.commit()
#         # Refresh the User object to get the updated ID
#         db.refresh(db_user)
#         # Close the database session
#         db.close()
#         # Serialize the user data (excluding the password field)
#         serialized_user = {"id": db_user.id, "username": db_user.username}
#         # Return a JSON response
#         return jsonify({"message": "User created successfully", "user": serialized_user})
#     except:
#         # Handle exceptions (e.g., IntegrityError) by rolling back the changes
#         db.rollback()
#         # Close the database session
#         db.close()
#         # Return an error response
#         return jsonify({"error": "Username already exists"}), 400
    

# # Define a Pydantic model for user login
# class LoginUser(BaseModel):
#     username: str
#     password: str

# # Define the login endpoint
# @app.route('/login/', methods=['POST'])
# def login():
#     # Parse JSON data from the request
#     login_data = request.json
#     # Create a Pydantic model instance
#     login_user = LoginUser(**login_data)

#     # Retrieve the user from the database based on the username
#     db_user = db.query(User).filter_by(username=login_user.username).first()

#     # Check if the user exists and the provided password is correct
#     if db_user and bcrypt.checkpw(login_user.password.encode('utf-8'), db_user.password.encode('utf-8')):
#         # Authentication successful
#         return jsonify({"message": "Login successful", "user_id": db_user.id})
#     else:
#         # Authentication failed
#         return jsonify({"error": "Invalid username or password"}), 401

# if __name__ == "__main__":
#     app.run(debug=True)


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

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        new_user = User(username=username, password=hashed_password)
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
