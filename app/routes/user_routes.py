from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.database import get_db_connection
from psycopg2.extras import RealDictCursor
import uuid
from datetime import datetime

user_bp = Blueprint('user', __name__)

@user_bp.route('/auth/login', methods=['POST'])
def user_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM user WHERE username = %s AND password = %s AND role = 'user'", (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user:
        from app import create_access_token
        access_token = create_access_token(identity={'id': user['id'], 'role': user['role'], 'group_id': user['group_id']})
        return jsonify({'access_token': access_token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@user_bp.route('/prompts', methods=['POST'])
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
        "INSERT INTO prompt (id, description, statut, prix, user_id, vote) VALUES (%s, %s, %s, %s, %s, %s)",
        (prompt_id, data['description'], 'EN_ATTENTE', 1000, identity['id'], 0)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Prompt crée', 'prompt_id': prompt_id}), 201

@user_bp.route('/prompts/<id>/delete-request', methods=['PUT'])
@jwt_required()
def request_prompt_deletion(id):
    identity = get_jwt_identity()
    if identity['role'] != 'user':
        return jsonify({'message': 'User access required'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM prompt WHERE id = %s AND user_id = %s", (id, identity['id']))
    prompt = cur.fetchone()
    
    if not prompt:
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt introuvable ou pas accees'}), 404
    
    cur.execute("UPDATE prompt SET statut = 'A_SUPPRIMER' WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Prompt suppression demandee'}), 200

@user_bp.route('/prompts/<id>/vote', methods=['POST'])
@jwt_required()
def vote_prompt(id):
    identity = get_jwt_identity()
    if identity['role'] != 'user':
        return jsonify({'message': 'User access required'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM prompt WHERE id = %s AND user_id != %s", (id, identity['id']))
    prompt = cur.fetchone()
    
    if not prompt:
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt introuvable ou pas acces'}), 404
    
    cur.execute("SELECT * FROM user WHERE id = %s", (identity['id'],))
    user = cur.fetchone()
    
    points = 2 if user['group_id'] == prompt['user_id'] else 1
    cur.execute(
        "INSERT INTO vote (prompt_id, user_id, vote_date) VALUES (%s, %s, %s)",
        (id, identity['id'], datetime.now())
    )
    
    cur.execute("SELECT SUM(CASE WHEN u.group_id = p.user_id THEN 2 ELSE 1 END) as total_points FROM vote v JOIN user u ON v.user_id = u.id JOIN prompt p ON v.prompt_id = p.id WHERE v.prompt_id = %s", (id,))
    total_points = cur.fetchone()['total_points'] or 0
    
    if total_points >= 6:
        cur.execute("UPDATE prompt SET statut = 'ACRIVER' WHERE id = %s", (id,))
    
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Vote enregistrer'}), 200

@user_bp.route('/prompts/<id>/rate', methods=['POST'])
@jwt_required()
def rate_prompt(id):
    identity = get_jwt_identity()
    if identity['role'] != 'user':
        return jsonify({'message': 'User access required'}), 403
    
    data = request.get_json()
    rating = data.get('rating')
    if not (-10 <= rating <= 10):
        return jsonify({'message': 'La note doit etre comprise entre -10 et 10'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM prompt WHERE id = %s AND user_id != %s AND statut = 'ACTIVER'", (id, identity['id']))
    prompt = cur.fetchone()
    
    if not prompt:
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt introuvable ou non activé'}), 404
    
    cur.execute("SELECT * FROM user WHERE id = %s", (identity['id'],))
    user = cur.fetchone()
    
    weight = 0.6 if user['group_id'] == prompt['user_id'] else 0.4
    weighted_rating = rating * weight
    
    cur.execute(
        "INSERT INTO notation (prompt_id, user_id, valeur_note, rating_date) VALUES (%s, %s, %s, %s)",
        (id, identity['id'], weighted_rating, datetime.now())
    )
    
    cur.execute("SELECT AVG(valeur_note) as avg_rating FROM notation WHERE prompt_id = %s", (id,))
    avg_rating = cur.fetchone()['avg_rating'] or 0
    
    new_price = 1000 * (1 + avg_rating)
    cur.execute("UPDATE prompt SET prix = %s, valeur_note = %s WHERE id = %s", (new_price, avg_rating, id))
    
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Notation enregistre'}), 200