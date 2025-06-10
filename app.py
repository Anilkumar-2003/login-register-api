from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import bcrypt

app = Flask(__name__)
CORS(app)

# MongoDB Configuration
MONGO_URI = "mongodb+srv://anilkumar:anilkumar@ecommerce.cngsbpv.mongodb.net/?retryWrites=true&w=majority&appName=talentpro"
client = MongoClient(MONGO_URI)
db = client.talenthuntpro

# Collections
users_collection = db.users
job_roles_collection = db.job_roles
applications_collection = db.applications

# Helper function to verify user
def verify_user(email, password):
    user = users_collection.find_one({'email': email})
    if not user:
        return None
    if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return None
    return user

# Auth Routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'guest')

        if not all([name, email, password]):
            return jsonify({'message': 'All fields are required'}), 400

        if users_collection.find_one({'email': email}):
            return jsonify({'message': 'User already exists'}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user_data = {
            'name': name,
            'email': email,
            'password': hashed_password,
            'role': role,
            'created_at': datetime.utcnow()
        }

        result = users_collection.insert_one(user_data)

        return jsonify({
            'message': 'User registered successfully',
            'user_id': str(result.inserted_id)
        }), 201

    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            return jsonify({'message': 'Email and password are required'}), 400

        user = verify_user(email, password)
        if not user:
            return jsonify({'message': 'Invalid credentials'}), 401

        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'role': user['role']
            }
        }), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Profile route with email auth for demo purpose
@app.route('/api/profile', methods=['POST'])
def get_profile():
    try:
        data = request.json
        email = data.get('email')
        user = users_collection.find_one({'email': email})
        if not user:
            return jsonify({'message': 'User not found'}), 404

        return jsonify({
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'role': user['role'],
                'created_at': user.get('created_at')
            }
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Job Roles
@app.route('/api/job-roles', methods=['GET'])
def get_job_roles():
    try:
        roles = list(job_roles_collection.find())
        for role in roles:
            role['id'] = str(role['_id'])
            del role['_id']
        return jsonify(roles), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/api/job-roles/<role_id>', methods=['GET'])
def get_job_role(role_id):
    try:
        role = job_roles_collection.find_one({'_id': ObjectId(role_id)})
        if not role:
            return jsonify({'message': 'Job role not found'}), 404

        applications = list(applications_collection.find({'job_role_id': role_id}))
        formatted_apps = [{
            'id': str(app['_id']),
            'candidate_id': app['candidate_id'],
            'status': app['status'],
            'applied_date': app['applied_date']
        } for app in applications]

        role['id'] = str(role['_id'])
        del role['_id']

        return jsonify({
            'role': role,
            'applications': formatted_apps
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/api/dashboard/metrics', methods=['POST'])
def get_dashboard_metrics():
    try:
        data = request.json
        email = data.get('email')
        user = users_collection.find_one({'email': email})
        if not user:
            return jsonify({'message': 'User not found'}), 404

        if user['role'] == 'hr':
            total_job_roles = job_roles_collection.count_documents({})
            total_applications = applications_collection.count_documents({})

            metrics = {
                'total_job_roles': total_job_roles,
                'total_applications': total_applications,
                'user_role': 'hr'
            }
        else:
            total_job_roles = job_roles_collection.count_documents({})
            metrics = {
                'total_job_roles': total_job_roles,
                'user_role': 'guest',
                'message': 'Limited access - Guest user'
            }

        return jsonify(metrics), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
