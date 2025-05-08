from flask import Blueprint, request, jsonify
from models.database import get_db_connection
from psycopg2.extras import RealDictCursor

visitor_bp = Blueprint('visiteur', __name__)

@visitor_bp.route('/prompts/<id>', methods=['GET'])
def get_prompt(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM prompt WHERE id = %s AND statut = 'Activer'", (id,))
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
    cur.execute("SELECT * FROM prompt WHERE statut = 'Activer'")
    prompts = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(prompts), 200

@visitor_bp.route('/prompts/search', methods=['GET'])
def search_prompts():
    keyword = request.args.get('q', '')
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM prompt WHERE statut = 'Activer' AND description ILIKE %s", (f'%{keyword}%',))
    prompts = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(prompts), 200

@visitor_bp.route('/prompts/<id>/purchase', methods=['POST'])
def purchase_prompt(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM prompt WHERE id = %s AND statut = 'Activer'", (id,))
    prompt = cur.fetchone()
    cur.close()
    conn.close()
    
    if prompt:
        return jsonify({'message': 'Prompt purchased', 'prompt': prompt}), 200
    return jsonify({'message': 'Prompt introuvable ou non activé'}), 404