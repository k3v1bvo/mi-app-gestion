import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__, static_folder='../static', static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret')

# Inicializar cliente de Supabase
supabase: Client = create_client(
    os.environ.get('SUPABASE_URL'),
    os.environ.get('SUPABASE_KEY')
)

# -------------------- Rutas para servir el frontend --------------------
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/groups')
def serve_groups():
    return send_from_directory(app.static_folder, 'groups.html')

@app.route('/person/new')
def serve_person_form():
    return send_from_directory(app.static_folder, 'person_form.html')

@app.route('/person/edit/<string:person_id>')
def serve_person_edit(person_id):
    return send_from_directory(app.static_folder, 'person_form.html')

@app.route('/group/new')
def serve_group_form():
    return send_from_directory(app.static_folder, 'groups_form.html')

@app.route('/group/edit/<string:group_id>')
def serve_group_edit(group_id):
    return send_from_directory(app.static_folder, 'groups_form.html')

# -------------------- API para grupos --------------------
@app.route('/api/groups', methods=['GET'])
def get_groups():
    try:
        response = supabase.table('groups').select('*').eq('esta_activo', True).execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups', methods=['POST'])
def create_group():
    data = request.json
    if not data.get('group_name'):
        return jsonify({'error': 'group_name es requerido'}), 400
    try:
        new_group = {
            'group_name': data['group_name'],
            'esta_activo': True
        }
        result = supabase.table('groups').insert(new_group).execute()
        return jsonify(result.data[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/<string:group_id>', methods=['PUT'])
def update_group(group_id):
    data = request.json
    try:
        update_data = {}
        if 'group_name' in data:
            update_data['group_name'] = data['group_name']
        result = supabase.table('groups').update(update_data).eq('code', group_id).execute()
        if not result.data:
            return jsonify({'error': 'Grupo no encontrado'}), 404
        return jsonify(result.data[0]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/<string:group_id>', methods=['DELETE'])
def delete_group(group_id):
    try:
        # Eliminación lógica: marcar como inactivo
        result = supabase.table('groups').update({'esta_activo': False}).eq('code', group_id).execute()
        if not result.data:
            return jsonify({'error': 'Grupo no encontrado'}), 404
        return jsonify({'message': 'Grupo eliminado'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# -------------------- API para personas --------------------
@app.route('/api/persons', methods=['GET'])
def get_persons():
    try:
        # Obtener todas las personas activas con datos del grupo
        response = supabase.table('persons').select('*, groups(group_name)').eq('esta_activo', True).execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/persons', methods=['POST'])
def create_person():
    data = request.json
    # Validaciones básicas
    if not data.get('names') or not data.get('email') or not data.get('group_id'):
        return jsonify({'error': 'Faltan campos obligatorios'}), 400
    # Verificar que el grupo exista y esté activo
    group = supabase.table('groups').select('code').eq('code', data['group_id']).eq('esta_activo', True).execute()
    if not group.data:
        return jsonify({'error': 'Grupo no válido'}), 400
    try:
        new_person = {
            'names': data['names'],
            'last_names': data.get('last_names', ''),
            'email': data['email'],
            'cellphone': data.get('cellphone', ''),
            'address': data.get('address', ''),
            'observations': data.get('observations', ''),
            'photograph': data.get('photograph', ''),  # Base64
            'group_id': data['group_id'],
            'esta_activo': True
        }
        result = supabase.table('persons').insert(new_person).execute()
        return jsonify(result.data[0]), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/persons/<string:person_id>', methods=['PUT'])
def update_person(person_id):
    data = request.json
    try:
        update_data = {}
        for field in ['names', 'last_names', 'email', 'cellphone', 'address', 'observations', 'photograph', 'group_id']:
            if field in data:
                update_data[field] = data[field]
        # No permitir cambiar esta_activo desde aquí
        result = supabase.table('persons').update(update_data).eq('code', person_id).execute()
        if not result.data:
            return jsonify({'error': 'Persona no encontrada'}), 404
        return jsonify(result.data[0]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/persons/<string:person_id>', methods=['DELETE'])
def delete_person(person_id):
    try:
        # Eliminación lógica
        result = supabase.table('persons').update({'esta_activo': False}).eq('code', person_id).execute()
        if not result.data:
            return jsonify({'error': 'Persona no encontrada'}), 404
        return jsonify({'message': 'Persona eliminada'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)