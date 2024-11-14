from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_bcrypt import Bcrypt  # Make sure to install flask-bcrypt
from db import SessionLocal, User
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from db import create
from serializers import get_all_serializer, serialize_user
from todos import bp
from users import users_bp
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user, login_required


app = Flask(__name__)
bcrypt = Bcrypt(app)
db = SessionLocal()

# Setup Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirects to login page


@login_manager.user_loader
def load_user(user_id):
    return db.query(User).get(int(user_id))

# Custom ModelView that requires login
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('render_login', next=request.url))


# Initialize Flask-Admin
admin = Admin(app, name='My Admin Panel', template_mode='bootstrap3')
# Your existing routes go here...

admin.add_view(ModelView(User, db))

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


@app.route('/register/', methods=['POST'])
def register_user():
    if request.is_json:
        # Handling JSON data
        user_data = request.json
        username = user_data.get('username')
        password = user_data.get('password')
        first_name = user_data.get('firstname')
        last_name = user_data.get('lastname')
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
        new_user = User(username=username, password=hashed_password, first_name=first_name, last_name=last_name,
                        email=email)
        create(db, new_user)
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

    if user and user.password_is_valid(password):
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"error": "Invalid username or password"}), 401



@app.route('/details/', methods=['GET'])
def get_detail_user():
    users = db.query(User).all()
    serialized_users = [get_all_serializer(user) for user in users]
    return jsonify({"users": serialized_users})


@app.route('/all/', methods=['GET'])
def all_users():
    users = db.query(User).all()
    serialize_users = [serialize_user(user) for user in users]
    return {"users": serialize_users}


@app.route('/update-user/<user_id>/', methods=['PATCH'])
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


@app.route('/get-user/', methods=['GET'])
def get_user():
    # Get the value of the 'user_id' query parameter
    user_id = request.args.get('user_id')
    if user_id:
        try:
            user = db.query(User).get(user_id)
            return jsonify([serialize_user(user)])
        except:
            return {"message": f"User not found with user_id : {user_id}"}
    else:
        return jsonify({"error": "Missing user_id parameter"}), 400


@app.route('/search-users', methods=['GET'])
def search_users():
    # Get the value of the 'q' query parameter
    query_param = request.args.get('q')

    if query_param:
        # Perform a partial match search on username, email, or any other fields
        users = db.query(User).filter(
            User.username.ilike(f'%{query_param}%'),
            User.email.ilike(f'%{query_param}%'))
        # Add more fields as needed

        # Serialize the result
        serialized_users = [serialize_user(user) for user in users]

        return jsonify({"status": 200, "results": len(serialized_users), "users": serialized_users}), 200
    else:
        return jsonify({"error": "Missing 'q' parameter"}), 400


app.register_blueprint(bp, url_prefix='/todos')
app.register_blueprint(users_bp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
