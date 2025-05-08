from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models.database import get_db_connection

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, role FROM user WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()

    if not user:
        return jsonify({"msg": "Invalid credentials"}), 401

    user_id, role = user
    token = create_access_token(identity={"id": user_id, "role": role})
    return jsonify(access_token=token), 200
