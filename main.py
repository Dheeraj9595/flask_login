from crypt import methods
from csv import excel
from os import error

import openpyxl
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_bcrypt import Bcrypt  # Make sure to install flask-bcrypt
from six import add_move
from werkzeug.utils import secure_filename

from account import account_bp
from db import SessionLocal, User, Bank_Account, Notifications
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from db import create
from serializers import get_all_serializer, serialize_user, RegisterUserSerializer
from todos import bp
from users import users_bp, user_serializer, user_return_serializer
from flask_login import UserMixin, LoginManager, login_user, logout_user, current_user, login_required
import pandas as pd

from utils import require_api_key

app = Flask(__name__)
bcrypt = Bcrypt(app)
db = SessionLocal()

# Setup Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirects to login page
app.config['SECRET_KEY'] = 'your_random_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'uploads/'


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

# @app.route('/home/', methods=['GET'])
# def render_home():
#     return render_template('home.html')

# Render login form
@app.route('/login/', methods=['GET'])
def render_login():
    return render_template('login_page.html')


@app.route('/register/', methods=['POST'])
def register_user():
    try:
        if request.is_json:
            user_data = request.get_json()
        else:
            user_data = request.form.to_dict()
        username = user_data.get("username")
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return jsonify({"message": "User with this username already registered"})
        else:
            validated_data = RegisterUserSerializer(**user_data)

            username = validated_data.username
            password = validated_data.password
            email = validated_data.email
            first_name = validated_data.first_name
            last_name = validated_data.last_name

            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            new_user = User(username=username,
                            password=hashed_password,
                            first_name=first_name,
                            last_name=last_name,
                            email=email
                            )
            create(db, new_user)
            return jsonify({"message": "User registered successfully"}), 200, {'Content-Type': 'application/json'}
    except IntegrityError as e:
        # Rollback and log the error
        db.rollback()
        print(f"Database error: {e}")
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
        return redirect(url_for('admin_users'))
        # return jsonify({"message": "aLogin successful"})
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
    count = len(users)
    return {"users": serialize_users, "User Count": count}


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

@app.route('/updateuser', methods=['PATCH'])
def update_user2():
    data = request.json
    user_id = data.get('user_id')
    username = data.get('username')
    email = data.get('email')

    user = db.query(User).filter(User.id==user_id).first()

    if user is None:
        return jsonify({"error": "User not found"}), 404

    user.username = username
    user.email = email

    db.commit()

    return jsonify({"message": "User updated successfully", "user": {"id": user.id, "username": user.username}}), 200





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



@app.route('/upload/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        return render_template('upload.html')

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and file.filename.endswith('.xlsx'):
            filename = secure_filename(file.filename)
            file_path = app.config['UPLOAD_FOLDER'] + filename
            file.save(file_path)

            #process the excel file using pandas
            try:
                df = pd.read_excel(file_path)
                for _,row in df.iterrows():
                    username = row.get('username')
                    password = row.get('password')

                    if username and password:
                        #now hash the password
                        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

                        #create a new user instance
                        new_user = User(username=username, password=hashed_password)

                        db.add(new_user)
                        db.commit()
                        db.save()
                flash('Users uploaded and saved successfully')
            except IntegrityError:
                db.rollback()
                flash("Error: some usres already exist or there was an issue with the data.")
            except Exception as e:
                flash(f"Error processing the file{str(e)}")
            finally:
                db.close()
            return redirect(url_for('upload_file'))
    return render_template('upload.html')

@app.route('/view', methods=['POST'])
def view():

    file = request.files['file']
    file.save(file.filename)
    data = pd.read_excel(file)
    return data.to_html()

@app.route('/save', methods=["POST"])
def save_users_from_file():
    """Upload and save users from an Excel file using Pandas."""
    # Check if a file is in the request
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    if not file.filename.endswith('.xlsx'):
        return jsonify({"error": "Only .xlsx files are supported"}), 400

    try:
        # Read the Excel file into a Pandas DataFrame
        df = pd.read_excel(file)

        # Ensure required columns exist
        required_columns = {'username', 'password'}
        if not required_columns.issubset(df.columns):
            return jsonify({"error": f"Missing required columns: {required_columns - set(df.columns)}"}), 400

        errors = []  # To track duplicates or issues
        users_to_add = []

        # Loop through the DataFrame rows
        for _, row in df.iterrows():
            # breakpoint()
            username = row['username']
            password = row['password']
            firstname = row['first_name']
            lastname = row['last_name']
            email = row['email']

            if pd.isna(username) or pd.isna(password):  # Skip rows with missing data
                continue

            # Check for existing user in the database
            existing_user = db.query(User).filter_by(username=username).first()

            if existing_user:
                errors.append(f"Duplicate username found: {username}")
            else:
                # Hash the password and prepare the User instance
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                user = User(username=username, password=hashed_password, last_name=lastname, first_name=firstname,email=email)
                users_to_add.append(user)

        # Add all new users to the database
        if users_to_add:
            db.add_all(users_to_add)
            db.commit()

        # Prepare the response
        response = {"message": f"Successfully saved {len(users_to_add)} users."}
        if errors:
            response["errors"] = errors

        return jsonify(response), 200

    except IntegrityError as e:
        db.rollback()
        return jsonify({"error": "Database integrity error", "details": str(e)}), 500

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    finally:
        db.close()

@app.route('/save_email', methods=['POST'])
def update_email_from_excel():
    file = request.files['file']
    try:
        # Step 1: Read the Excel file to get the emails
        # Assuming the Excel file has a column "email" for new email addresses
        df = pd.read_excel(file)

        # Check if the email column exists
        if 'email' not in df.columns:
            return jsonify({"error": "The Excel file does not contain an 'email' column."}), 400

        # Step 2: Query users whose email is NULL
        users_to_update = db.query(User).filter(User.email == None).all()

        # Check if there are users to update
        if not users_to_update:
            return jsonify({"message": "No users without an email."}), 404

        # Step 3: Update users' email addresses
        for i, user in enumerate(users_to_update):
            if i < len(df):  # Ensure we don't go out of bounds if there are more users than emails
                user.email = df.iloc[i]['email']  # Assign email from Excel to the user
            else:
                break  # Stop if we've run out of emails

        # Step 4: Commit the changes to the database
        db.commit()

        # Return a success message
        return jsonify({"message": f"Email updated for {len(users_to_update)} users."})

    except Exception as e:
        db.rollback()  # Rollback the transaction in case of error
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        db.close()  # Close the session

import os


@app.route('/export_users', methods=['GET'])
def export_user_data():
    # Query user data from the database
    users = db.query(User).all()
    response = [user_return_serializer(user) for user in users]
    file_path = 'test_excel.xlsx'

    # Check if the file exists and is a valid Excel file
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            # Handle case where file exists but isn't a valid Excel file
            print(f"Error reading Excel file: {e}")
            df = pd.DataFrame(columns=['id', 'name', 'email', 'created_date'])
    else:
        # If file doesn't exist, create an empty DataFrame
        df = pd.DataFrame(columns=['id', 'name', 'email', 'created_date'])

    # Append the new data to the DataFrame
    df = pd.concat([df, pd.DataFrame(response)], ignore_index=True)

    # Write the updated DataFrame back to the Excel file
    df.to_excel(file_path, index=False, engine='openpyxl')

    # Return the user data as a JSON response
    return jsonify(response)


@app.route('/')
# @login_required
def admin_users():
    return render_template('index.html')


@app.route('/login_page')
def login_page():
    return render_template('login_page.html')

@app.route('/bulk-create', methods=['POST'])
def bulk_user_create():
    try:
        users_data = request.get_json()

        if not users_data:
            return jsonify({"message": "Please provide user data"})
        users = []
        existing_users = []
        for user_data in users_data:
            username = user_data.get('username')
            password = user_data.get('password')
            email = user_data.get('email')
            firstname = user_data.get('first_name')
            lastname = user_data.get('last_name')

            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            #check if user already exists

            existing = db.query(User).filter(User.username== username).first()

            if existing:
                existing_users.append(existing)
                continue

            #create a new user instance
            new_user = User(username=username,
                            password=hashed_password,
                            email=email,
                            first_name=firstname,
                            last_name=lastname)
            users.append(new_user)
        db.bulk_save_objects(users)
        db.commit()
        return jsonify({"message": f"{len(users)} Users saved successfully {existing_users} already registerd!!!"})
    except IntegrityError as e:
        db.rollback()
        return jsonify(
            {"error": "Integrity error occurred. Likely duplicate usernames or emails.", "details": str(e)}), 400

    except Exception as e:
        db.rollback()
        return jsonify({"error": "An error occurred while creating users.", "details": str(e)}), 500

    finally:
        db.close()

@app.route('/delete/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = db.query(User).filter(User.id==user_id).first()
        if user is None:
            return jsonify({"message": "user with user id {user_id} is deleted or not existed!!!"})
        if user:
            db.delete(user)
            db.commit()
        return jsonify({"message": f"user with user_id: {user_id} and username: {user.username}  is deleted successfully!!!"})
    except Exception as e:
        return jsonify({"message": f"there is a error {str(e)}"})

    finally:
        db.close()

@app.route('/delete', methods=['DELETE'])
def delete_multiple():
    try:
        users_list = request.get_json()
        message = []
        # breakpoint()
        for user in users_list:
            user = db.query(User).filter(User.id==user).first()
            if user is None:
                message.append({"message": f"user with user id {user.id} not found"})
            if user:
                db.delete(User)
                db.commit()
            message.append({"message": f"user with user id {user.id} is deleted successfully"})
    except Exception as e:
        return jsonify({"message": f"there is a error {str(e)}"})

    finally:
        db.close()


app.register_blueprint(bp, url_prefix='/todos')
app.register_blueprint(account_bp)
app.register_blueprint(users_bp)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
