from flask import Blueprint, request, jsonify
from db import db, Todo, create, User

bp = Blueprint("todos", __name__, url_prefix="/todo/")


@bp.route("/create-todo/", methods=["POST"])
def create_todo():
    data = request.json

    user_id = data.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        db.close()
        return jsonify({"error": "User not found"}), 404

    todo_data = {
        "title": data.get("title"),
        "description": data.get("description"),
        "due_date": data.get("due_date"),
        "completed": data.get("completed"),
        "user": user,
    }
    todo = Todo(**todo_data)
    create(db, todo)
    return jsonify({"message": "Todo created successfully...", "todo_id": todo.id})


from collections import OrderedDict


def todos_serializer(todo):
    return OrderedDict(
        [
            ("todo id", todo.id),
            ("todo user", todo.user_id),
            ("todo title", todo.title),
            ("todo description", todo.description),
            ("todo due date", todo.due_date),
            ("completed", todo.completed),
        ]
    )


@bp.route("/all/", methods=["GET"])
def show_todos():
    try:
        todos = db.query(Todo).all()
        serializer = [todos_serializer(todo) for todo in todos]
        return {"todos": serializer}
    except Exception as e:
        return {f"todos can't be created due to {str(e)}"}
