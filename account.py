from flask import request, jsonify, Blueprint

from db import User, SessionLocal, Bank_Account, Notifications
from utils import require_api_key

db = SessionLocal()

# users_bp = Blueprint('users', __name__, url_prefix='/users')
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
        notifications = db.query(Notifications).filter(Notifications.user_id == user_id).all()
        notifications_serializer = [{"id": user.id, "message": user.content} for user in notifications]
        return jsonify(notifications_serializer)
    except Exception as e:
        return jsonify({"message": f"Error is {str(e)}"})