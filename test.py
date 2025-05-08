from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
jwt = JWTManager(app)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="prompt_api",
        user="postgres",
        password="your_password"
    )
    return conn

# Admin Endpoints
@app.route('/auth/login', methods=['POST'])
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
        access_token = create_access_token(identity={'id': user['id'], 'role': user['role']})
        return jsonify({'access_token': access_token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/users', methods=['POST'])
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

@app.route('/users', methods=['GET'])
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

@app.route('/users/<id>', methods=['PUT'])
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

@app.route('/users/<id>', methods=['DELETE'])
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

@app.route('/groups', methods=['POST'])
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

@app.route('/groups', methods=['GET'])
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

@app.route('/groups/<id>', methods=['PUT'])
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

@app.route('/groups/<id>', methods=['DELETE'])
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

@app.route('/prompts', methods=['GET'])
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

@app.route('/prompts/<id>/validate', methods=['PUT'])
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

@app.route('/prompts/<id>/review', methods=['PUT'])
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

@app.route('/prompts/<id>', methods=['DELETE'])
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

# User Endpoints
@app.route('/auth/login', methods=['POST'])
def user_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Users WHERE username = %s AND password = %s AND role = 'user'", (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user:
        access_token = create_access_token(identity={'id': user['id'], 'role': user['role'], 'group_id': user['group_id']})
        return jsonify({'access_token': access_token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/prompts', methods=['POST'])
@jwt_required()
def create_prompt():
    identity = get_jwt_identity()
    if identity['role'] != 'user':
        return jsonify({'message': 'User access required'}), 403
    
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    prompt_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO Prompts (id, content, state, price, user_id, rating) VALUES (%s, %s, %s, %s, %s, %s)",
        (prompt_id, data['content'], 'En attente', 1000, identity['id'], 0)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Prompt created', 'prompt_id': prompt_id}), 201

@app.route('/prompts/<id>/delete-request', methods=['PUT'])
@jwt_required()
def request_prompt_deletion(id):
    identity = get_jwt_identity()
    if identity['role'] != 'user':
        return jsonify({'message': 'User access required'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Prompts WHERE id = %s AND user_id = %s", (id, identity['id']))
    prompt = cur.fetchone()
    
    if not prompt:
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt not found or not owned'}), 404
    
    cur.execute("UPDATE Prompts SET state = 'À supprimer' WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Prompt deletion requested'}), 200

@app.route('/prompts/<id>/vote', methods=['POST'])
@jwt_required()
def vote_prompt(id):
    identity = get_jwt_identity()
    if identity['role'] != 'user':
        return jsonify({'message': 'User access required'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Prompts WHERE id = %s AND user_id != %s", (id, identity['id']))
    prompt = cur.fetchone()
    
    if not prompt:
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt not found or own prompt'}), 404
    
    cur.execute("SELECT * FROM Users WHERE id = %s", (identity['id'],))
    user = cur.fetchone()
    
    points = 2 if user['group_id'] == prompt['user_id'] else 1
    cur.execute(
        "INSERT INTO Votes (prompt_id, user_id, vote_date) VALUES (%s, %s, %s)",
        (id, identity['id'], datetime.now())
    )
    
    cur.execute("SELECT SUM(CASE WHEN u.group_id = p.user_id THEN 2 ELSE 1 END) as total_points FROM Votes v JOIN Users u ON v.user_id = u.id JOIN Prompts p ON v.prompt_id = p.id WHERE v.prompt_id = %s", (id,))
    total_points = cur.fetchone()['total_points'] or 0
    
    if total_points >= 6:
        cur.execute("UPDATE Prompts SET state = 'Activer' WHERE id = %s", (id,))
    
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Vote recorded'}), 200

@app.route('/prompts/<id>/rate', methods=['POST'])
@jwt_required()
def rate_prompt(id):
    identity = get_jwt_identity()
    if identity['role'] != 'user':
        return jsonify({'message': 'User access required'}), 403
    
    data = request.get_json()
    rating = data.get('rating')
    if not (-10 <= rating <= 10):
        return jsonify({'message': 'Rating must be between -10 and 10'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Prompts WHERE id = %s AND user_id != %s AND state = 'Activer'", (id, identity['id']))
    prompt = cur.fetchone()
    
    if not prompt:
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt not found, own prompt, or not activated'}), 404
    
    cur.execute("SELECT * FROM Users WHERE id = %s", (identity['id'],))
    user = cur.fetchone()
    
    weight = 0.6 if user['group_id'] == prompt['user_id'] else 0.4
    weighted_rating = rating * weight
    
    cur.execute(
        "INSERT INTO Ratings (prompt_id, user_id, rating, rating_date) VALUES (%s, %s, %s, %s)",
        (id, identity['id'], weighted_rating, datetime.now())
    )
    
    cur.execute("SELECT AVG(rating) as avg_rating FROM Ratings WHERE prompt_id = %s", (id,))
    avg_rating = cur.fetchone()['avg_rating'] or 0
    
    new_price = 1000 * (1 + avg_rating)
    cur.execute("UPDATE Prompts SET price = %s, rating = %s WHERE id = %s", (new_price, avg_rating, id))
    
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Rating recorded'}), 200

# Visitor Endpoints
@app.route('/prompts/<id>', methods=['GET'])
def get_prompt(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Prompts WHERE id = %s AND state = 'Activer'", (id,))
    prompt = cur.fetchone()
    cur.close()
    conn.close()
    
    if prompt:
        return jsonify(prompt), 200
    return jsonify({'message': 'Prompt not found or not activated'}), 404

@app.route('/prompts', methods=['GET'])
def list_activated_prompts():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Prompts WHERE state = 'Activer'")
    prompts = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(prompts), 200

@app.route('/prompts/search', methods=['GET'])
def search_prompts():
    keyword = request.args.get('q', '')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Prompts WHERE state = 'Activer' AND content ILIKE %s", (f'%{keyword}%',))
    prompts = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(prompts), 200

@app.route('/prompts/<id>/purchase', methods=['POST'])
def purchase_prompt(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM Prompts WHERE id = %s AND state = 'Activer'", (id,))
    prompt = cur.fetchone()
    cur.close()
    conn.close()
    
    if prompt:
        return jsonify({'message': 'Prompt purchased', 'prompt': prompt}), 200
    return jsonify({'message': 'Prompt not found or not activated'}), 404

if __name__ == '__main__':
    app.run(debug=True)