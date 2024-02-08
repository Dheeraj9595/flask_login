from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, func
import datetime


DATABASE_URL = "mysql+mysqlconnector://admin:Root*1234@localhost:3306/flask_login"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

db = SessionLocal()


class AbstractModel(Base):
    __abstract__= True
    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, default=func.now(), server_default=func.now())

class User(AbstractModel):
    __tablename__ = "user"
    first_name = Column(String(50), index=True)
    last_name = Column(String(50), index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(200), index=True)

    def __repr__(self):
        return '<User %r' % self.username

# Create database tables
Base.metadata.create_all(bind=engine)

