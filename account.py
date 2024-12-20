import json
import os

from flask import request, jsonify, Blueprint
from starlette import requests

from db import User, SessionLocal, Bank_Account, Notifications
from serializers import RegisterUserSerializer, UpdateUserSerializer
from utils import require_api_key
from sqlalchemy.orm import joinedload

db = SessionLocal()

account_bp = Blueprint("account", __name__, url_prefix="")


@account_bp.route("/open-account", methods=["POST"])
def open_bank_account():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        initial_amount = data.get("initial_amount")
        if not user_id and initial_amount:
            return jsonify({"message": "user id and initial amount are mandatory"})
        new_account = Bank_Account(user_id=user_id, account_balance=initial_amount)
        notification = Notifications(
            content=f"+ Deposited {initial_amount}.", user_id=user_id
        )
        db.add(notification)
        db.add(new_account)
        db.commit()
        return jsonify({"message": "your account is now open with our bank thank you."})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

    finally:
        db.close()


@account_bp.route("/deposit", methods=["POST"])
@require_api_key
def deposit():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        balance_to_add = data.get("deposit_amount")

        # Validate input
        if not user_id or balance_to_add is None:
            return (
                jsonify({"message": "Please provide user_id and deposit_amount"}),
                400,
            )

        if balance_to_add <= 0:
            return jsonify({"message": "Deposit amount must be positive"}), 400

        # Retrieve the bank account from the database
        bank_acc = db.query(Bank_Account).filter_by(user_id=user_id).first()
        if not bank_acc:
            return jsonify({"message": "Bank account not found"}), 404

        # Update the balance
        bank_acc.add_balance(balance_to_add)
        notification = Notifications(
            content=f"+ Deposited {balance_to_add}.", user_id=user_id
        )
        db.add(notification)
        db.commit()

        return (
            jsonify(
                {
                    "message": f"Account balance updated for user {user_id}",
                    "new_balance": bank_acc.account_balance,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

    finally:
        db.close()


@account_bp.route("/withdrawal", methods=["POST"])
@require_api_key
def withdrawal():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        amount = data.get("amount")
        atm_pin = data.get("atm_pin")

        # input validation with all the required fields
        if not user_id or not amount or not atm_pin:
            return jsonify(
                {"message": "user_id, amount and atm_pin are mandatory please provide"}
            )

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"message": "User not found"}), 404

        # atm pin validation
        if user.atm_pin != atm_pin:
            return jsonify({"message": "ATM pin is not correct or invalid"}), 403

        bank_account = (
            db.query(Bank_Account).filter(Bank_Account.user_id == user_id).first()
        )
        if not bank_account:
            return jsonify({"message": "Bank account not found"}), 404

        # Perform withdrawal
        if amount <= 0:
            return jsonify({"message": "Withdrawal amount must be positive"}), 400

        if bank_account.account_balance < amount:
            return jsonify({"message": "Insufficient funds"}), 400

        bank_account.withdrawal(amount)

        # Create a notification
        notification = Notifications(content=f"- Withdrew {amount}.", user_id=user_id)
        db.add(notification)

        # Commit changes
        db.commit()

        # Return success response
        return (
            jsonify(
                {
                    "message": f"Amount {amount} has been deducted from your account balance.",
                    "updated_balance": bank_account.account_balance,
                }
            ),
            200,
        )

    except Exception as e:
        db.rollback()
        return jsonify({"message": f"Error: {str(e)}"}), 500


@account_bp.route("/balance/<user_id>", methods=["GET"])
@require_api_key
def check_balance(user_id):
    user_id = user_id
    try:
        try:
            user_obj = (
                db.query(Bank_Account).filter(Bank_Account.user_id == user_id).first()
            )
        except Exception as e:
            return jsonify({"message": f"Error {str(e)}"})
        if not user_obj:
            return jsonify(
                {
                    "message": f"Bank Account with user id {user_id} is not found in database"
                }
            )
        balance_of_user = user_obj.balance
        if balance_of_user:
            return jsonify({"balance": f"user balance is {balance_of_user}"})
        return jsonify({"message": "user balance is 0"})
    except Exception as e:
        return jsonify({"message": f"Error {str(e)}"})
    finally:
        db.close()


@account_bp.route("/generate_pin", methods=["POST"])
@require_api_key
def generate_atm_pin():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        atm_pin = data.get("atm_pin")
        if not user_id:
            return jsonify(
                {
                    "message": "user id is mandatory to generate atm pin please provide atm pin"
                }
            )
        user_obj = db.query(User).filter(User.id == user_id).first()
        user_obj.atm_pin = atm_pin
        db.commit()
        return jsonify(
            {"message": f"Your atm pin is set successfully pin is {atm_pin}"}
        )
    except Exception as e:
        return jsonify({"message": f"Error is {str(e)}"})


@account_bp.route("/user-notification/<user_id>", methods=["GET"])
def user_notification(user_id):
    try:
        if not user_id:
            return jsonify({"message": "user id is mandatory"})
        notifications = (
            db.query(Notifications)
            .filter(Notifications.user_id == user_id)
            .order_by(Notifications.created_date.desc())
            .all()
        )
        notifications_serializer = [
            {"id": user.id, "message": user.content} for user in notifications
        ]
        return jsonify(notifications_serializer)
    except Exception as e:
        return jsonify({"message": f"Error is {str(e)}"})


@account_bp.route("/bankaccounts", methods=["GET"])
@require_api_key
def all_bank_accounts():
    try:
        bank_accounts = db.query(Bank_Account).all()
        bank_account_serializer = [
            {"user_id": user.id, "balance": user.account_balance}
            for user in bank_accounts
        ]
        return jsonify({"data": bank_account_serializer})
    except Exception as e:
        return jsonify({"message": f"Error is {str(e)}"})
    finally:
        db.close()


import requests


@account_bp.route("/bankacc/<user_id>/", methods=["GET"])
def specific_bank_account(user_id):
    try:
        response = requests.get(
            "http://localhost:5000/bankaccounts",
            headers={"x-api-key": os.environ.get("api_key")},
        )
        data = response.json()
        users_data = data.get("data", [])
        for user_data in users_data:
            if user_data["user_id"] == int(user_id):
                data = user_data["balance"]
                return jsonify({"account_balance": data})
        return jsonify({"message": f"user not found with given user id {user_id}"})
    except Exception as e:
        return jsonify({"message": f"Error is {str(e)}"})


@account_bp.route("/depositapi", methods=["POST"])
def deposit_amount_using_api():
    try:
        # Parse and validate input
        data = request.get_json()
        user_id = data.get("user_id")
        deposit_amount = data.get("deposit_amount")
        if not user_id or not deposit_amount:
            return jsonify({"message": "user_id and deposit_amount are required"}), 400
        if deposit_amount <= 0:
            return jsonify({"message": "Deposit amount must be greater than zero"}), 400
        api_key = os.environ.get("api_key")
        if not api_key:
            return jsonify({"message": "API key not configured"}), 500
        headers = {"Content-Type": "application/json", "x-api-key": api_key}
        payload = {"user_id": user_id, "deposit_amount": deposit_amount}
        deposit_response = requests.post(
            url="http://localhost:5000/deposit", json=payload, headers=headers
        )
        if deposit_response.status_code != 200:
            return (
                jsonify(
                    {
                        "message": "Failed to deposit amount",
                        "details": deposit_response.json().get(
                            "message", "Unknown error"
                        ),
                    }
                ),
                deposit_response.status_code,
            )
        updated_balance = deposit_response.json().get("new_balance")
        if updated_balance is None:
            return (
                jsonify(
                    {"message": "Deposit succeeded but balance information is missing"}
                ),
                500,
            )
        return (
            jsonify(
                {
                    "message": f"Your balance has been updated by {deposit_amount} for user_id: {user_id}.",
                    "updated_balance": updated_balance,
                }
            ),
            200,
        )
    except requests.exceptions.RequestException as req_err:
        return jsonify({"message": f"API Request Error: {str(req_err)}"}), 500
    except Exception as e:
        return jsonify({"message": f"Unexpected Error: {str(e)}"}), 500


@account_bp.route("/transfer-balance", methods=["POST"])
def balance_transfer():
    try:

        # take the args from json from user id to user id and balance and atm pin
        data = request.get_json()
        from_user_id = data.get("from_user_id")
        to_user_id = data.get("to_user_id")
        amount = data.get("amount")
        atm_pin = data.get("atm_pin")

        # Validate input
        if not all([from_user_id, to_user_id, amount, atm_pin]):
            return (
                jsonify(
                    {
                        "error": "Missing required fields [from_user_id, to_user_id, amount, atm_pin] all fields are required"
                    }
                ),
                400,
            )

        from_account = (
            db.query(Bank_Account).filter(Bank_Account.user_id == from_user_id).first()
        )
        from_user = db.query(User).filter(User.id == from_user_id).first()
        to_user = db.query(User).filter(User.id == to_user_id).first()
        if from_user.atm_pin != atm_pin:
            return jsonify({"message": "Invalid ATM Pin"})
        # balance transfer
        result = from_account.balance_transfer(
            from_user_id=from_user_id, to_user_id=to_user_id, amount=amount
        )
        return jsonify(
            {
                "message": f"Successfully transferred {amount} from user {from_user.username} to user {to_user.username}",
                "from_user_balance": result["from_user_balance"],
                "to_user_balance": result["to_user_balance"],
            }
        )
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


# #Todo make atm pin reset feature
@account_bp.route("/forget-password", methods=["POST"])
def reset_atm_pin():
    try:
        # parse the incoming data
        data = request.get_json()
        username = data.get("username")

        # check if username is provided
        if not username:
            return jsonify({"message": "username is mandatory"}), 400

        # Query the user from database
        user = db.query(User).filter(User.username == username).first()
        if not user or user is None:
            return jsonify({"message": "user not found with given username"})

        # Generate new atm pin
        new_pin = user.atm_pin_generator()

        # Ensure the user has registered email
        user_email = user.email
        if not user_email:
            return jsonify(
                {
                    "message": "User email is mandatory please provide email to send reset atm pin"
                }
            )

        # Update the user's atm_pin in database
        user.atm_pin = new_pin
        db.commit()
        headers = {"Content-Type": "application/json"}
        payload = {
            "subject": "test email",
            "recipient": user_email,
            "body": f"Your new ATM pin is: {new_pin}. Please keep it secure.",
        }
        response = requests.post(
            url="http://localhost:5000/send-email", json=payload, headers=headers
        )

        if response.status_code == 200:
            return (
                jsonify(
                    {
                        "message": f"Reset ATM pin has been sent to your email: {user_email}"
                    }
                ),
                200,
            )
        else:
            return (
                jsonify({"message": "Failed to send email. Please try again later."}),
                500,
            )

    except Exception as e:
        return jsonify({"message": f"Error : {str(e)}"})


@account_bp.route("/change-password", methods=["POST"])
def change_password():
    from flask_bcrypt import bcrypt, Bcrypt
    from main import app

    bcrypt = Bcrypt(app)
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        # get user instance
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"message": f"user with {user_id} not found in database"})
        if not old_password and new_password:
            return jsonify({"message": "old password and new password is mandatory"})
        hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        if user.password_is_valid(old_password):
            user.password = hashed_password
            db.commit()
            return jsonify(
                {
                    "message": f"Password for {user.username} has been changed successfully...!!!"
                }
            )
        else:
            return jsonify({"message": "old password is not correct"})
    except Exception as e:
        return jsonify({"message": f"Error : {str(e)}"})


@account_bp.route('/eligibility', methods=['GET'])
def check_loan_eligibility():
    try:
        eligible_users = (
            db.query(User)
            .options(joinedload(User.bank_accounts))  # Eager load bank accounts
            .filter(User.bank_accounts.any(Bank_Account.account_balance > 300000))
            .all()
        )
        if not eligible_users:
            return jsonify({"message": "there are no users with eligiblity criteria"})
        response = []
        for user in eligible_users:
            response.append(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "bank_accounts": [
                        {
                            "account_id": account.id,
                            "account_balance": account.account_balance,
                        }
                        for account in user.bank_accounts
                        if account.account_balance > 300000
                    ],
                }
            )
        return jsonify(
            {"message": "List of eligible users", "eligible_users": response}
        )
    except Exception as e:
        return jsonify({"message": f"Error : {str(e)}"})


@account_bp.route('/update-user/<int:user_id>', methods=['PATCH'])
def update_user(user_id: int):
    data = request.get_json()
    try:
        user_data = UpdateUserSerializer(**data)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    user = db.query(User).get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Update only the fields that are provided in the request
    if 'username' in data:
        user.username = user_data.username

    # Optionally, you could handle password, email, first_name, and last_name
    # but only if those fields are provided in the request

    if 'password' in data:  # Only update password if it's in the payload
        user.password = user_data.password

    if 'email' in data:  # Only update email if it's in the payload
        user.email = user_data.email

    if 'first_name' in data:  # Only update first_name if it's in the payload
        user.first_name = user_data.first_name

    if 'last_name' in data:  # Only update last_name if it's in the payload
        user.last_name = user_data.last_name
    db.commit()
    return jsonify({"message": "User updated successfully"}), 200


