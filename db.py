from operator import index

from flask_bcrypt import Bcrypt
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, \
    func, Boolean, orm
import datetime
from flask import jsonify
from sqlalchemy.exc import IntegrityError
import random

DATABASE_URL = "sqlite:///flasklogin.sqlite"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

db = SessionLocal()
bcrypt = Bcrypt()


class AbstractModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default=func.now(), server_default=func.now())


class User(AbstractModel):
    __tablename__ = "user"
    first_name = Column(String(50), index=True)
    last_name = Column(String(50), index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=False, index=True)
    password = Column(String(200), index=True)
    todos = relationship("Todo", back_populates="user")
    atm_pin = Column(Integer, index=True)
    is_active = Column(Boolean, default=True, index=True)
    bank_accounts = relationship("Bank_Account", back_populates="user")

    def __repr__(self):
        return '<User %r' % self.username

    def password_is_valid(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def atm_pin_generator(self):
        pin = random.randint(1000, 9999)
        self.atm_pin = pin
        return pin


class Todo(AbstractModel):
    __tablename__ = "todos"
    title = Column(String(255), nullable=False)
    description = Column(String(1000))
    due_date = Column(DateTime)
    completed = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey('user.id'))  # Assuming you have a 'users' table

    # Define a relationship with the User model (assuming you have a User model)
    user = relationship("User", back_populates="todos")


class Notifications(AbstractModel):
    __tablename__ = "notifications"
    content = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))


class Bank_Account(AbstractModel):
    __tablename__ = "bank_account"
    account_balance = Column(Integer, index=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", back_populates="bank_accounts")

    @property
    def balance(self):
        # Getter for account balance
        return self.account_balance

    def withdrawal(self, amount):
        if amount <= 0:
            raise ValueError('Withdrawal amount should be more than zero')
        self.account_balance -= amount

    def add_balance(self, deposite_amount):
        if deposite_amount <= 0:
            raise ValueError('Deposite amount must be postive')
        self.account_balance += deposite_amount

    def balance_transfer(self, from_user_id, to_user_id, amount):
        if amount <= 0:
            raise ValueError("Transfer amount must be greater than zero")

        from_account = db.query(Bank_Account).filter(Bank_Account.user_id == from_user_id).first()
        to_account = db.query(Bank_Account).filter(Bank_Account.user_id == to_user_id).first()
        from_user = db.query(User).filter(User.id == from_user_id).first()
        to_user = db.query(User).filter(User.id == to_user_id).first()

        if not from_account or not to_account:
            raise ValueError("One or both users do not have a bank account")

        if from_account.account_balance < amount:
            raise ValueError("Insufficient balance for transfer")

        try:
            from_account.withdrawal(amount)
            # Create a notification
            notification = Notifications(
                content=f"- Amount {amount} and transferred to {to_user.username}.",
                user_id=from_user_id
            )
            db.add(notification)
            to_account.add_balance(amount)
            notification = Notifications(
                content=f"- Amount {amount} Deposited from {from_user.username}.",
                user_id=to_user_id
            )
            db.add(notification)
            db.commit()
            return {
                "from_user_balance": from_account.balance,
                "to_user_balance": to_account.balance,
            }
        except Exception as e:
            db.rollback()
            raise ValueError(f"Transfer failed: {str(e)}")


# Create database tables
Base.metadata.create_all(bind=engine)


def create(database, item):
    try:
        database.add(item)
        database.commit()
        database.refresh(item)
        return jsonify({"message": f"{item} created successfully"})
    except IntegrityError:
        database.rollback()
        return jsonify({"error": "IntegrityError - Duplicate entry"}), 400
    except Exception as e:
        database.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        database.close()
