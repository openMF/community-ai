from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
import json
from models.speech_recognition import recognize_speech
from models.intent_recognition import extract_intent, preprocess_text
from models.voice_biometrics import authenticate_voice, enroll_user_voice
from services.banking_service import process_banking_request
from services.user_service import get_user_by_id, authenticate_user, create_user, update_user_language
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/audio'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Ensure data directory exists
data_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(data_dir, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html)

@app.route('/api/process-voice', methods=['POST'])
def process_voice():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    if not audio_file or not audio_file.filename:
        return jsonify({'error': 'Invalid audio file'}), 400
        
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
        
    language = request.form.get('language', 'en-US')  # Default to English
    
    # Save audio file temporarily with a unique name to avoid conflicts
    original_filename = secure_filename(audio_file.filename)
    filename = f"{os.path.splitext(original_filename)[0]}_{os.urandom(4).hex()}{os.path.splitext(original_filename)[1]}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        audio_file.save(filepath)
        
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return jsonify({'error': 'Failed to save audio file or file is empty'}), 500
        
        # Step 1: Authenticate voice
        auth_result = authenticate_voice(filepath, user_id)
        if not auth_result['authenticated']:
            return jsonify({'error': 'Voice authentication failed'}), 401
        
        # Step 2: Speech recognition
        text = recognize_speech(filepath, language)
        
        # Check if there was a speech recognition error
        if text and text.startswith('Error processing speech:'):
            return jsonify({'error': text}), 500
        
        # Preprocess text for display
        preprocessed_text = preprocess_text(text)
        
        # Step 3: Intent recognition
        intent_data = extract_intent(text, language)
        
        # Step 4: Process banking request
        user = get_user_by_id(user_id)
        response = process_banking_request(intent_data, user)
        
        return jsonify({
            'recognized_text': text,
            'preprocessed_text': preprocessed_text,
            'intent': intent_data,
            'response': response
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Clean up the temporary file
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                app.logger.error(f"Failed to remove temporary file {filepath}: {str(e)}")

# New routes for user authentication and management
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400
    
    user = authenticate_user(username, password)
    
    if user:
        # Remove password hash before sending to client
        user_data = {k: v for k, v in user.items() if k != 'password_hash'}
        return jsonify({'success': True, 'user': user_data})
    else:
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    language = data.get('language', 'en-US')
    
    if not all([username, password, name, email, phone]):
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    result = create_user(username, password, name, email, phone, language)
    
    if result['success']:
        return jsonify({'success': True, 'user_id': result['user_id']})
    else:
        return jsonify({'success': False, 'message': result['message']}), 400

@app.route('/api/update-language', methods=['POST'])
def update_language():
    data = request.json
    user_id = data.get('user_id')
    language = data.get('language')
    
    if not user_id or not language:
        return jsonify({'success': False, 'message': 'User ID and language required'}), 400
    
    result = update_user_language(user_id, language)
    return jsonify(result)

@app.route('/api/enroll-voice', methods=['POST'])
def enroll_voice():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    user_id = request.form.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID required'}), 400
    
    # Save audio file temporarily
    filename = secure_filename(audio_file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio_file.save(filepath)
    
    try:
        result = enroll_user_voice(filepath, user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        # Clean up the temporary file
        if os.path.exists(filepath):
            os.remove(filepath)

# Add a health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify the server is running."""
    status = {
        'status': 'ok',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'services': {
            'voice_recognition': True,
            'database': os.path.exists(os.path.join(os.path.dirname(__file__), 'data'))
        }
    }
    return jsonify(status)

# Add error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Use environment variable PORT if available (Render will set this)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
