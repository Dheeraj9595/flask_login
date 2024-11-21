
def user_serializer(user):
    return {"username": user.username, "email": user.email, "name": user.first_name + user.last_name}


def get_all_serializer(user):
    return {"id": user.id,
            "username": user.username,
            "first name": user.first_name,
            "last name": user.last_name}

def user_serializer(user):
    return {"id": user.id,
            "username": user.username,
            "email": user.email,
            "created_date": user.created_date}


def serialize_user(user):
    return {"id": user.id, "username": user.username, "email": user.email}

from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class RegisterUserSerializer(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)  # Mandatory
    password: str = Field(..., min_length=6)  # Mandatory
    email: EmailStr  # Mandatory, with automatic email validation
    first_name: Optional[str] = None  # Optional
    last_name: Optional[str] = None  # Optional
