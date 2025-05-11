from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models.database import get_db_connection
from psycopg2.extras import RealDictCursor
from flask_jwt_extended import create_access_token
import bcrypt
import uuid
from datetime import datetime

user_bp = Blueprint('Utilisateur', __name__)

# Fonction pour vérifier un mot de passe
def check_password(password, hashed_password):
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


@user_bp.route('/user/login', methods=['POST'])
def user_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM users WHERE username = %s AND role = 'Utilisateur'", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and check_password(password, user['password']):
        access_token = create_access_token(
            identity=str(user['id']),
            additional_claims={"role": user["role"]}
        )
        return jsonify({'access_token': access_token}), 200

    return jsonify({'message': 'Invalid credentials'}), 401


@user_bp.route('/prompts', methods=['POST'])
@jwt_required()
def create_prompt():
    role = get_jwt().get("role")
    user_id = int(get_jwt_identity()) 
    if role!= 'Utilisateur':
        return jsonify({'message': 'User access required'}), 403
    
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO prompt (description, prix, statut, user_id, moyenne_note) VALUES (%s, %s, %s, %s, %s)",
        (data['description'],1000, 'EN_ATTENTE',user_id, 0)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Prompt crée'}), 201

@user_bp.route('/prompts/<id>/delete-request', methods=['PUT'])
@jwt_required()
def request_prompt_deletion(id):
    role = get_jwt().get("role")
    user_id = int(get_jwt_identity()) 
    if role!= 'Utilisateur':
        return jsonify({'message': 'User access required'}), 403
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM prompt WHERE id = %s AND user_id = %s", (id, user_id))
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
    from datetime import datetime

    role = get_jwt().get("role")
    user_id = int(get_jwt_identity()) 
    if role != 'Utilisateur':
        return jsonify({'message': 'Accès en tant que Utilisateur requis'}), 403

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM prompt WHERE id = %s AND user_id != %s AND statut = %s", (id, user_id, "EN_ATTENTE"))
    prompt = cur.fetchone()

    if not prompt:
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt introuvable ou accès refusé'}), 404

    # Récupérer le groupe du votant
    cur.execute("SELECT group_id FROM users WHERE id = %s", (user_id,))
    groupe_votant = cur.fetchone()

    # Récupérer le groupe du créateur du prompt
    cur.execute("SELECT group_id FROM users WHERE id = %s", (prompt['user_id'],))
    groupe_createur_prompt = cur.fetchone()

    # Ici on va calculer les points
    points = 2 if groupe_votant['group_id'] == groupe_createur_prompt['group_id'] else 1

    # Enregistrement du vote
    cur.execute(
        "INSERT INTO vote (prompt_id, user_id, vote_date, points) VALUES (%s, %s, %s, %s)",
        (id, user_id, datetime.now(), points)
    )

    # Calcul du total des points pour ce prompt
    cur.execute(
        "SELECT SUM(CASE WHEN u.group_id = uc.group_id THEN 2 ELSE 1 END) as total_points "
        "FROM vote v "
        "JOIN users u ON v.user_id = u.id "
        "JOIN prompt p ON v.prompt_id = p.id "
        "JOIN users uc ON p.user_id = uc.id "
        "WHERE v.prompt_id = %s",
        (id,)
    )
    total_points = cur.fetchone()['total_points'] or 0

    # Changement de statut prompt
    if total_points >= 6:
        cur.execute("UPDATE prompt SET statut = 'ACTIVER' WHERE id = %s", (id,))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'message': 'Vote enregistré'}), 200


@user_bp.route('/prompts/<id>/noter', methods=['POST'])
@jwt_required()
def noter_prompt(id):
    role = get_jwt().get("role")
    user_id = int(get_jwt_identity()) 
    if role!= 'Utilisateur':
        return jsonify({'message': 'Accés en tant que Utilisateur requis'}), 403
    
    data = request.get_json()
    rating = data.get('rating')
    if not (-10 <= rating <= 10):
        return jsonify({'message': 'La note doit etre comprise entre -10 et 10'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM prompt WHERE id = %s AND user_id != %s AND statut = 'ACTIVER'", (id, user_id))
    prompt = cur.fetchone()
    
    if not prompt:
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt introuvable ou non activé'}), 404
    
    cur.execute("SELECT * FROM user WHERE id = %s", (user_id,))
    user = cur.fetchone()
    
    weight = 0.6 if user['group_id'] == prompt['user_id'] else 0.4
    weighted_rating = rating * weight
    
    cur.execute(
        "INSERT INTO notation (prompt_id, user_id, valeur_note, date_note) VALUES (%s, %s, %s, %s)",
        (id, user_id, weighted_rating, datetime.now())
    )
    
    cur.execute("SELECT AVG(valeur_note) as moyenne_note FROM notation WHERE prompt_id = %s", (id,))
    moyenne_note = cur.fetchone()['moyenne_note'] or 0
    
    new_price = 1000 * (1 + moyenne_note)
    cur.execute("UPDATE prompt SET prix = %s, moyenne_note = %s WHERE id = %s", (new_price, moyenne_note, id))
    
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Notation enregistre'}), 200

@user_bp.route('/prompts/<id>', methods=['GET'])
def get_prompt(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM prompt WHERE id = %s AND statut = 'ACTIVER'", (id,))
    prompt = cur.fetchone()
    cur.close()
    conn.close()
    
    if prompt:
        return jsonify(prompt), 200
    return jsonify({'message': 'Prompt introuvable ou non activé'}), 404