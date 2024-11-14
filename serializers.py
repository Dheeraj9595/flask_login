
def user_serializer(user):
    return {"username": user.username, "email": user.email, "name": user.first_name + user.last_name}


def get_all_serializer(user):
    return {"id": user.id,
            "username": user.username,
            "first name": user.first_name,
            "last name": user.last_name}


def serialize_user(user):
    return {"id": user.id, "username": user.username, "email": user.email}