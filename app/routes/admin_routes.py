from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity,get_jwt
from app.models.database import get_db_connection
from psycopg2.extras import RealDictCursor
from flask_jwt_extended import create_access_token
import uuid
import bcrypt

admin_bp = Blueprint('Administrateur', __name__)

# Fonction utilitaire pour hacher les mots de passe
def hash_password(password):
    # Génère un mot de passe haché
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')  # Mot de passe robuste qu'on va stocker

# Fonction pour vérifier un mot de passe
def check_password(password, hashed_password):
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

@admin_bp.route('/admin/create', methods=['POST'])
# Route facultative pour commencer avec la création d'un administrateur
def create_admin():
    data = request.get_json()
    
    # Hachage du mot de passe avant stockage
    hashed_password = hash_password(data['password'])
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "INSERT INTO users (username, prenom, nom, password, role, group_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (data['username'], data['prenom'], data['nom'], hashed_password, 'Administrateur', data.get('group_id'))
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Administrateur créé'}), 201
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': f'Erreur lors de la création: {str(e)}'}), 500

@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # On récupère l'utilisateur uniquement par son nom d'utilisateur
    cur.execute("SELECT * FROM users WHERE username = %s AND role = 'Administrateur'", (username, ))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    # Vérification du mot de passe avec bcrypt
    if user and check_password(password, user['password']):
        access_token = create_access_token(
        identity=str(user['id']),
        additional_claims={"role": user["role"]}
        )
        return jsonify({'access_token': access_token}), 200
    
    return jsonify({'message': 'Identifiants invalides'}), 401

@admin_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    role = get_jwt().get("role")
    if role!= 'Administrateur':
        return jsonify({'message': 'Accès administrateur requis'}), 403
    
    data = request.get_json()
    
    # Hachage du mot de passe avant stockage
    hashed_password = hash_password(data['password'])
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "INSERT INTO users (username, prenom, nom, password, role, group_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (data['username'], data['prenom'], data['nom'], hashed_password, data['role'], data.get('group_id'))
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Utilisateur créé'}), 201
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': f'Erreur lors de la création: {str(e)}'}), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    role = get_jwt().get("role")
    if role!= 'Administrateur':
        return jsonify({'message': 'Accès administrateur requis'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, username, prenom, nom, role, group_id FROM users")  # Ne pas renvoyer les mots de passe hachés
    users = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(users), 200

@admin_bp.route('/users/<id>', methods=['PUT'])
@jwt_required()
def update_user(id):
    role = get_jwt().get("role")
    if role!= 'Administrateur':
        return jsonify({'message': 'Accès administrateur requis'}), 403
    
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Vérifier si le mot de passe doit être mis à jour
        if 'password' in data and data['password']:
            hashed_password = hash_password(data['password'])
            cur.execute(
                "UPDATE users SET username = %s, prenom = %s, nom = %s, password = %s, role = %s, group_id = %s WHERE id = %s",
                (data['username'], data['prenom'], data['nom'], hashed_password, data['role'], data.get('group_id'), id)
            )
        else:
            # Si pas de nouveau mot de passe, on ne modifie pas ce champ
            cur.execute(
                "UPDATE users SET username = %s, prenom = %s, nom = %s, role = %s, group_id = %s WHERE id = %s",
                (data['username'], data['prenom'], data['nom'], data['role'], data.get('group_id'), id)
            )
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Utilisateur mis à jour'}), 200
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': f'Erreur lors de la mise à jour: {str(e)}'}), 500

@admin_bp.route('/users/<id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    role = get_jwt().get("role")
    if role!= 'Administrateur':
        return jsonify({'message': 'Accès administrateur requis'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM users WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Utilisateur supprimé'}), 200
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': f'Erreur lors de la suppression: {str(e)}'}), 500

@admin_bp.route('/groupes', methods=['POST'])
@jwt_required()
def create_group():
    role = get_jwt().get("role")
    if role!= 'Administrateur':
        return jsonify({'message': 'Accès administrateur requis'}), 403
    
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            'INSERT INTO groupe (nom_groupe) VALUES (%s)',
            (data['nom_groupe'],)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Groupe créé'}), 201
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': f'Erreur lors de la création du groupe: {str(e)}'}), 500

@admin_bp.route('/groupes', methods=['GET'])
@jwt_required()
def list_groups():
    role = get_jwt().get("role")
    if role!= 'Administrateur':
        return jsonify({'message': 'Accès administrateur requis'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute('SELECT * FROM groupe')
        groups = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(groups), 200
    except Exception as e:
        cur.close()
        conn.close()
        return jsonify({'message': f'Erreur lors de la récupération des groupes: {str(e)}'}), 500

@admin_bp.route('/groupes/<id>', methods=['PUT'])
@jwt_required()
def update_group(id):
    role = get_jwt().get("role")
    if role!= 'Administrateur':
        return jsonify({'message': 'Accès administrateur requis'}), 403
    
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('UPDATE groupe SET nom_groupe = %s WHERE id = %s', (data['nom_groupe'], id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Groupe mis à jour'}), 200
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': f'Erreur lors de la mise à jour du groupe: {str(e)}'}), 500

@admin_bp.route('/groupes/<id>', methods=['DELETE'])
@jwt_required()
def delete_group(id):
    role = get_jwt().get("role")
    if role!= 'Administrateur':
        return jsonify({'message': 'Accès administrateur requis'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM groupe WHERE id = %s', (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Groupe supprimé'}), 200
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': f'Erreur lors de la suppression du groupe: {str(e)}'}), 500

@admin_bp.route('/prompts', methods=['GET'])
@jwt_required()
def list_all_prompts():
    role = get_jwt().get("role")
    if role!= 'Administrateur':
        return jsonify({'message': 'Accès administrateur requis'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("SELECT * FROM prompt")
        prompts = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(prompts), 200
    except Exception as e:
        cur.close()
        conn.close()
        return jsonify({'message': f'Erreur lors de la récupération des prompts: {str(e)}'}), 500

@admin_bp.route('/prompts/<id>/validate', methods=['PUT'])
@jwt_required()
def validate_prompt(id):
    role = get_jwt().get("role")
    if role!= 'Administrateur':
        return jsonify({'message': 'Accès administrateur requis'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("UPDATE prompt SET statut = 'ACTIVER' WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt validé'}), 200
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': f'Erreur lors de la validation du prompt: {str(e)}'}), 500

@admin_bp.route('/prompts/<id>/review', methods=['PUT'])
@jwt_required()
def review_prompt(id):
    role = get_jwt().get("role")
    if role!= 'Administrateur':
        return jsonify({'message': 'Accès administrateur requis'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("UPDATE prompt SET statut = 'A_REVOIR' WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt mis à REVOIR'}), 200
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': f'Erreur lors de la mise à jour du statut du prompt: {str(e)}'}), 500

@admin_bp.route('/prompts/<id>', methods=['DELETE'])
@jwt_required()
def delete_prompt(id):
    role = get_jwt().get("role")
    if role!= 'Administrateur':
        return jsonify({'message': 'Accès administrateur requis'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM prompt WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt supprimé'}), 200
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': f'Erreur lors de la suppression du prompt: {str(e)}'}), 500