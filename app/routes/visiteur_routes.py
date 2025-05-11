from flask import Blueprint, request, jsonify
from app.models.database import get_db_connection
from psycopg2.extras import RealDictCursor
from datetime import date

visitor_bp = Blueprint('visiteur', __name__)

@visitor_bp.route('/prompts/<id>', methods=['GET'])
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

@visitor_bp.route('/prompts', methods=['GET'])
def list_activated_prompts():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM prompt WHERE statut = 'ACTIVER'")
    prompts = cur.fetchall()
    cur.close()
    conn.close()

    if prompts:
        return jsonify(prompts), 200
    return jsonify({'message': 'Aucun prompt activé trouvé'}), 404

@visitor_bp.route('/prompts/search', methods=['GET'])
def search_prompts():
    keyword = request.args.get('q', '')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM prompt WHERE statut = 'ACTIVER' AND description ILIKE %s", (f'%{keyword}%',))
    prompts = cur.fetchall()
    cur.close()
    conn.close()

    if prompts:
        return jsonify(prompts), 200
    return jsonify({'message': 'Aucun prompt trouvé avec ces mots clés'}); 404

@visitor_bp.route('/prompts/<id>/achat', methods=['POST'])
def achat_prompt(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Vérifier que le prompt est activé
    cur.execute("SELECT * FROM prompt WHERE id = %s AND statut = 'ACTIVER'", (id,))
    prompt = cur.fetchone()

    if not prompt:
        cur.close()
        conn.close()
        return jsonify({'message': 'Prompt introuvable ou non activé'}), 404

    # Ici on recupere l'adresse ip du visiteur pour avoir une trace
    visiteur_ip = request.remote_addr

    # Insérer l'achat avec une trace visiteur
    cur.execute(
        "INSERT INTO achat (prompt_id, prix, date_achat, source) VALUES (%s, %s, %s, %s)",
        (id, prompt['prix'], date.today(), f"visiteur_{visiteur_ip}")
    )

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'message': 'Prompt acheté', 'prompt': prompt}), 200