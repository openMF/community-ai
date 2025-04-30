import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Path to users database file
USERS_DB_PATH = os.path.join(os.path.dirname(__file__), '../data/users.json')

def load_users_db():
    """Load user database or create if it doesn't exist."""
    if not os.path.exists(USERS_DB_PATH):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(USERS_DB_PATH), exist_ok=True)
        
        # Create sample users
        users = {
            '1': {
                'id': '1',
                'username': 'johndoe',
                'password_hash': generate_password_hash('password123'),
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '+1234567890',
                'language': 'en-US'
            },
            '2': {
                'id': '2',
                'username': 'janesmith',
                'password_hash': generate_password_hash('password456'),
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'phone': '+0987654321',
                'language': 'hi-IN'
            }
        }
        
        with open(USERS_DB_PATH, 'w') as f:
            json.dump(users, f, indent=2)
    
    with open(USERS_DB_PATH, 'r') as f:
        return json.load(f)

def get_user_by_id(user_id):
    """Get user by ID."""
    users = load_users_db()
    return users.get(str(user_id))

def get_user_by_username(username):
    """Get user by username."""
    users = load_users_db()
    for user in users.values():
        if user['username'] == username:
            return user
    return None

def authenticate_user(username, password):
    """Authenticate a user with username and password."""
    user = get_user_by_username(username)
    if not user:
        return None
    
    if check_password_hash(user['password_hash'], password):
        return user
    
    return None

def create_user(username, password, name, email, phone, language='en-US'):
    """Create a new user."""
    users = load_users_db()
    
    # Check if username exists
    for user in users.values():
        if user['username'] == username:
            return {'success': False, 'message': 'Username already exists'}
    
    # Create new user
    new_user_id = str(max(int(uid) for uid in users.keys()) + 1) if users else '1'
    users[new_user_id] = {
        'id': new_user_id,
        'username': username,
        'password_hash': generate_password_hash(password),
        'name': name,
        'email': email,
        'phone': phone,
        'language': language
    }
    
    # Save to file
    with open(USERS_DB_PATH, 'w') as f:
        json.dump(users, f, indent=2)
    
    return {'success': True, 'user_id': new_user_id}

def update_user_language(user_id, language):
    """Update user's preferred language."""
    users = load_users_db()
    if str(user_id) not in users:
        return {'success': False, 'message': 'User not found'}
    
    users[str(user_id)]['language'] = language
    
    with open(USERS_DB_PATH, 'w') as f:
        json.dump(users, f, indent=2)
    
    return {'success': True}
