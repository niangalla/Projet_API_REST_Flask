from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models.database import get_db_connection
from psycopg2.extras import RealDictCursor
from flask_jwt_extended import create_access_token
import bcrypt
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

@user_bp.route('/prompts/<id>', methods=['PUT'])
@jwt_required()
def update_prompt(id):
    role = get_jwt().get("role")
    user_id = int(get_jwt_identity()) 
    if role!= 'Utilisateur':
        return jsonify({'message': 'User access required'}), 403
    
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM prompt WHERE id = %s AND user_id = %s AND statut = %s", (id, user_id, "A_REVOIR"))
    my_prompt = cur.fetchone()

    if not my_prompt:
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt introuvable ou pas accees'}), 404
    
    # On fait les modifications aprés on remet l'etat à EN_ATTENTE
    cur.execute("UPDATE prompt SET description = %s AND statut = %s WHERE id = %s", (data['description'], 'EN_ATTENTE', id)) 
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Prompt modifié'}), 201

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
    role = get_jwt().get("role")
    user_id = int(get_jwt_identity()) 

    if role != 'Utilisateur':
        return jsonify({'message': 'Accès en tant que Utilisateur requis'}), 403

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Vérifier que le prompt existe, est EN_ATTENTE, et ne vient pas de l'utilisateur connecté
    cur.execute("SELECT * FROM prompt WHERE (id = %s AND user_id != %s) AND (statut = %s OR statut = %s)", (id, user_id, "EN_ATTENTE", "RAPPEL"))
    prompt = cur.fetchone()

    if not prompt:
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt introuvable ou vote refusé'}), 404

    # Vérifier que l'utilisateur n'a pas déjà voté pour ce prompt
    cur.execute("SELECT 1 FROM vote WHERE prompt_id = %s AND user_id = %s", (id, user_id))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'message': 'Vous avez déjà voté pour ce prompt'}), 400

    # Récupérer les groupes
    cur.execute("SELECT group_id FROM users WHERE id = %s", (user_id,))
    groupe_votant = cur.fetchone()['group_id']

    cur.execute("SELECT group_id FROM users WHERE id = %s", (prompt['user_id'],))
    groupe_createur = cur.fetchone()['group_id']

    # Calcul des points
    points = 2 if groupe_votant == groupe_createur else 1

    # Enregistrer le vote
    cur.execute(
        "INSERT INTO vote (prompt_id, user_id, vote_date, points) VALUES (%s, %s, %s, %s)",
        (id, user_id, datetime.now(), points)
    )

    # Calcul des points cumulés pour le prompt
    cur.execute("SELECT SUM(points) as total_points FROM vote WHERE prompt_id = %s", (id,))
    total_points = cur.fetchone()['total_points'] or 0

    # Activer le prompt si total points atteint 6
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
    note = data.get('valeur_note')
    if not (-10 <= note <= 10):
        return jsonify({'message': 'La note doit etre comprise entre -10 et 10'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM prompt WHERE id = %s AND user_id != %s AND statut = 'ACTIVER'", (id, user_id))
    prompt = cur.fetchone()
    
    if not prompt:
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt introuvable ou non activé'}), 404
    
    # Vérifier que l'utilisateur n'a pas déjà noté ce prompt
    cur.execute("SELECT 1 FROM notation WHERE prompt_id = %s AND user_id = %s", (id, user_id))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'message': 'Vous avez déjà noté ce prompt'}), 400
    
    # Récupérer les groupes
    cur.execute("SELECT group_id FROM users WHERE id = %s", (user_id,))
    groupe_votant = cur.fetchone()['group_id']

    cur.execute("SELECT group_id FROM users WHERE id = %s", (prompt['user_id'],))
    groupe_createur = cur.fetchone()['group_id']
    
    poids = 0.6 if groupe_votant == groupe_createur else 0.4
    poids_note = note * poids
    
    cur.execute(
        "INSERT INTO notation (prompt_id, user_id, valeur_note, date_note) VALUES (%s, %s, %s, %s)",
        (id, user_id, poids_note, datetime.now())
    )
    
    cur.execute("SELECT AVG(valeur_note) as moyenne_note FROM notation WHERE prompt_id = %s", (id,))
    moyenne_note = cur.fetchone()['moyenne_note'] or 0
    
    nouveau_prix = 1000 * (1 + moyenne_note)
    cur.execute("UPDATE prompt SET prix = %s, moyenne_note = %s WHERE id = %s", (nouveau_prix, moyenne_note, id))
    
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