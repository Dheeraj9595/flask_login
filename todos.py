from flask import Blueprint, render_template


todos_bp = Blueprint("todos", __name__, url_prefix="/api/todos/")



# Render todo form
@todos_bp.route('/todo/', methods=['GET'])
def render_todo():
    return render_template('index.html')
