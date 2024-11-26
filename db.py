from operator import index

from flask_bcrypt import Bcrypt
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, \
    func, Boolean
import datetime
from flask import jsonify
from sqlalchemy.exc import IntegrityError

DATABASE_URL = "sqlite:///flasklogin.sqlite"


engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

db = SessionLocal()
bcrypt= Bcrypt()

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

    def __repr__(self):
        return '<User %r' % self.username

    def password_is_valid(self, password):
        return bcrypt.check_password_hash(self.password, password)

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

    @property
    def balance(self):
        # Getter for account balance
        return self.account_balance


    def withdrawal(self, amount):
        if amount <=0:
            raise ValueError('Withdrawal amount should be more than zero')
        self.account_balance -= amount

    def add_balance(self, deposite_amount):
        if deposite_amount <=0:
            raise ValueError('Deposite amount must be postive')
        self.account_balance += deposite_amount

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
