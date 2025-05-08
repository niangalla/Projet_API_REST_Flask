from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.database import get_db_connection
from psycopg2.extras import RealDictCursor
import uuid

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/auth/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Users WHERE username = %s AND password = %s AND role = 'admin'", (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user:
        from app import create_access_token
        access_token = create_access_token(identity={'id': user['id'], 'role': user['role']})
        return jsonify({'access_token': access_token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@admin_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Users (id, username, password, role, group_id) VALUES (%s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), data['username'], data['password'], data['role'], data.get('group_id'))
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'User created'}), 201

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Users")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(users), 200

@admin_bp.route('/users/<id>', methods=['PUT'])
@jwt_required()
def update_user(id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE Users SET username = %s, password = %s, role = %s, group_id = %s WHERE id = %s",
        (data['username'], data['password'], data['role'], data.get('group_id'), id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'User updated'}), 200

@admin_bp.route('/users/<id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Users WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'User deleted'}), 200

@admin_bp.route('/groups', methods=['POST'])
@jwt_required()
def create_group():
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Groups (id, name) VALUES (%s, %s)",
        (str(uuid.uuid4()), data['name'])
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Group created'}), 201

@admin_bp.route('/groups', methods=['GET'])
@jwt_required()
def list_groups():
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Groups")
    groups = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(groups), 200

@admin_bp.route('/groups/<id>', methods=['PUT'])
@jwt_required()
def update_group(id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Groups SET name = %s WHERE id = %s", (data['name'], id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Group updated'}), 200

@admin_bp.route('/groups/<id>', methods=['DELETE'])
@jwt_required()
def delete_group(id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Groups WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Group deleted'}), 200

@admin_bp.route('/prompts', methods=['GET'])
@jwt_required()
def list_all_prompts():
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Prompts")
    prompts = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(prompts), 200

@admin_bp.route('/prompts/<id>/validate', methods=['PUT'])
@jwt_required()
def validate_prompt(id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Prompts SET state = 'Activer' WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Prompt validated'}), 200

@admin_bp.route('/prompts/<id>/review', methods=['PUT'])
@jwt_required()
def review_prompt(id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Prompts SET state = 'À revoir' WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Prompt set to review'}), 200

@admin_bp.route('/prompts/<id>', methods=['DELETE'])
@jwt_required()
def delete_prompt(id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify({'message': 'Admin access required'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Prompts WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Prompt deleted'}), 200