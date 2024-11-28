import json
import os
from crypt import methods

from flask import request, jsonify, Blueprint
from starlette import requests

from db import User, SessionLocal, Bank_Account, Notifications
from utils import require_api_key

db = SessionLocal()

account_bp = Blueprint('account', __name__, url_prefix='')



@account_bp.route('/open-account', methods=['POST'])
def open_bank_account():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        initial_amount = data.get('initial_amount')
        if not user_id and initial_amount:
            return jsonify({"message": "user id and initial amount are mandatory"})
        new_account = Bank_Account(user_id= user_id,
                                   account_balance= initial_amount)
        notification = Notifications(
            content=f"+ Deposited {initial_amount}.",
            user_id=user_id
        )
        db.add(notification)
        db.add(new_account)
        db.commit()
        return jsonify({"message": "your account is now open with our bank thank you."})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

    finally:
        db.close()

@account_bp.route('/deposit', methods=['POST'])
@require_api_key
def deposit():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        balance_to_add = data.get('deposit_amount')

        # Validate input
        if not user_id or balance_to_add is None:
            return jsonify({"message": "Please provide user_id and deposit_amount"}), 400

        if balance_to_add <= 0:
            return jsonify({"message": "Deposit amount must be positive"}), 400

        # Retrieve the bank account from the database
        bank_acc = db.query(Bank_Account).filter_by(user_id=user_id).first()
        if not bank_acc:
            return jsonify({"message": "Bank account not found"}), 404

        # Update the balance
        bank_acc.add_balance(balance_to_add)
        notification = Notifications(
            content=f"+ Deposited {balance_to_add}.",
            user_id = user_id
        )
        db.add(notification)
        db.commit()

        return jsonify(
            {"message": f"Account balance updated for user {user_id}", "new_balance": bank_acc.account_balance}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

    finally:
        db.close()

@account_bp.route('/withdrawal', methods=['POST'])
@require_api_key
def withdrawal():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        amount = data.get('amount')
        atm_pin = data.get('atm_pin')

        #input validation with all the required fields
        if not user_id or not amount or not atm_pin:
            return jsonify({"message": "user_id, amount and atm_pin are mandatory please provide"})

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"message": "User not found"}),404

        #atm pin validation
        if user.atm_pin != atm_pin:
            return jsonify({"message": "ATM pin is not correct or invalid"}),403

        bank_account = db.query(Bank_Account).filter(Bank_Account.user_id == user_id).first()
        if not bank_account:
            return jsonify({"message": "Bank account not found"}), 404

        #Perform withdrawal
        if amount <= 0:
            return jsonify({"message": "Withdrawal amount must be positive"}), 400

        if bank_account.account_balance < amount:
            return jsonify({"message": "Insufficient funds"}), 400

        bank_account.withdrawal(amount)

        # Create a notification
        notification = Notifications(
                    content=f"- Withdrew {amount}.",
                    user_id=user_id
                )
        db.add(notification)

        # Commit changes
        db.commit()

        # Return success response
        return jsonify({
                    "message": f"Amount {amount} has been deducted from your account balance.",
                    "updated_balance": bank_account.account_balance
                }), 200

    except Exception as e:
            db.rollback()
            return jsonify({"message": f"Error: {str(e)}"}), 500



@account_bp.route('/balance/<user_id>', methods=['GET'])
@require_api_key
def check_balance(user_id):
    user_id = user_id
    try:
        try:
            user_obj = db.query(Bank_Account).filter(Bank_Account.user_id==user_id).first()
        except Exception as e:
            return jsonify({"message": f"Error {str(e)}"})
        if not user_obj:
            return jsonify({"message": f"User with user id {user_id} is not found in database"})
        balance_of_user = user_obj.balance
        if balance_of_user:
            return jsonify({"balance": f"user balance is {balance_of_user}"})
        return jsonify({"message": "user balance is 0"})
    except Exception as e:
        return jsonify({"message": f"Error {str(e)}"})
    finally:
        db.close()

@account_bp.route('/generate_pin', methods=['POST'])
@require_api_key
def generate_atm_pin():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        atm_pin = data.get("atm_pin")
        if not user_id:
            return jsonify({"message": "user id is mandatory to generate atm pin please provide atm pin"})
        user_obj = db.query(User).filter(User.id == user_id).first()
        user_obj.atm_pin = atm_pin
        db.commit()
        return jsonify({"message": f"Your atm pin is set successfully pin is {atm_pin}"})
    except Exception as e:
        return jsonify({"message": f"Error is {str(e)}"})

@account_bp.route('/user-notification/<user_id>', methods=['GET'])
def user_notification(user_id):
    try:
        if not user_id:
            return jsonify({"message": "user id is mandatory"})
        notifications = (db.query(Notifications)
                         .filter(Notifications.user_id == user_id)
                         .order_by(Notifications.created_date.desc())
                         .all())
        notifications_serializer = [{"id": user.id, "message": user.content} for user in notifications]
        return jsonify(notifications_serializer)
    except Exception as e:
        return jsonify({"message": f"Error is {str(e)}"})

@account_bp.route('/bankaccounts', methods=['GET'])
@require_api_key
def all_bank_accounts():
    try:
        bank_accounts = db.query(Bank_Account).all()
        bank_account_serializer = [{"user_id": user.id, "balance": user.account_balance} for user in bank_accounts]
        return jsonify({"data": bank_account_serializer})
    except Exception as e:
        return jsonify({"message": f"Error is {str(e)}"})
    finally:
        db.close()

import requests

@account_bp.route('/bankacc/<user_id>/', methods=['GET'])
def specific_bank_account(user_id):
    try:
        response = requests.get('http://localhost:5000/bankaccounts', headers={'x-api-key': os.environ.get('api_key')})
        data = response.json()
        users_data = data.get('data', [])
        for user_data in users_data:
            if user_data['user_id'] == int(user_id):
                data = user_data['balance']
                return jsonify({"account_balance": data})
        return jsonify({"message": f"user not found with given user id {user_id}"})
    except Exception as e:
        return jsonify({"message": f"Error is {str(e)}"})

# @account_bp.route('/depositapi', methods=['POST'])
# def deposite_amount_using_api():
#     try:
#         data = request.get_json()
#         user_id = data.get('user_id')
#         deposit_amount = data.get('deposit_amount')
#         payload = {"user_id": user_id, "deposit_amount": deposit_amount}
#         headers = {'Content-Type': 'application/json'}
#         api_key = os.environ.get('api_key')  # Replace with your function to retrieve the key
#         headers['x-api-key'] = api_key
#         response = requests.post(url='http://localhost:5000/deposit', data=json.dumps(payload), headers=headers)
#         updated_balance = requests.get(url=f'http://localhost:5000/balance/{user_id}', headers=headers)
#
#         return jsonify({"message": f"your balance is updated with {deposit_amount} for user_id : {user_id} and updated balance is {updated_balance.json().get('balance')}"})
#     except Exception as e:
#         return jsonify({"message": f"Error is {str(e)}"})

@account_bp.route('/depositapi', methods=['POST'])
def deposit_amount_using_api():
    try:
        # Parse and validate input
        data = request.get_json()
        user_id = data.get('user_id')
        deposit_amount = data.get('deposit_amount')
        if not user_id or not deposit_amount:
            return jsonify({"message": "user_id and deposit_amount are required"}), 400
        if deposit_amount <= 0:
            return jsonify({"message": "Deposit amount must be greater than zero"}), 400
        api_key = os.environ.get('api_key')
        if not api_key:
            return jsonify({"message": "API key not configured"}), 500
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key
        }
        payload = {
            "user_id": user_id,
            "deposit_amount": deposit_amount
        }
        deposit_response = requests.post(
            url='http://localhost:5000/deposit',
            json=payload,
            headers=headers
        )
        if deposit_response.status_code != 200:
            return jsonify({
                "message": "Failed to deposit amount",
                "details": deposit_response.json().get('message', 'Unknown error')
            }), deposit_response.status_code
        updated_balance = deposit_response.json().get('new_balance')
        if updated_balance is None:
            return jsonify({
                "message": "Deposit succeeded but balance information is missing"
            }), 500
        return jsonify({
            "message": f"Your balance has been updated by {deposit_amount} for user_id: {user_id}.",
            "updated_balance": updated_balance
        }), 200
    except requests.exceptions.RequestException as req_err:
        return jsonify({"message": f"API Request Error: {str(req_err)}"}), 500
    except Exception as e:
        return jsonify({"message": f"Unexpected Error: {str(e)}"}), 500


@account_bp.route('/transfer-balance', methods=['POST'])
def balance_transfer():
    try:

        #take the args from json from user id to user id and balance and atm pin
        data = request.get_json()
        from_user_id = data.get('from_user_id')
        to_user_id = data.get('to_user_id')
        amount = data.get('amount')
        atm_pin = data.get('atm_pin')

        # Validate input
        if not all([from_user_id, to_user_id, amount, atm_pin]):
            return jsonify({"error": "Missing required fields [from_user_id, to_user_id, amount, atm_pin] all fields are required"}), 400

        from_account = db.query(Bank_Account).filter(Bank_Account.user_id == from_user_id).first()
        from_user = db.query(User).filter(User.id == from_user_id).first()
        to_user = db.query(User).filter(User.id == to_user_id).first()
        if from_user.atm_pin != atm_pin:
            return jsonify({"message": "Invalid ATM Pin"})
        #balance transfer
        result = from_account.balance_transfer(from_user_id=from_user_id,
                                               to_user_id=to_user_id,
                                               amount=amount)
        return jsonify({
            "message": f"Successfully transferred {amount} from user {from_user.username} to user {to_user.username}",
            "from_user_balance": result["from_user_balance"],
            "to_user_balance": result["to_user_balance"]
        })
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500



