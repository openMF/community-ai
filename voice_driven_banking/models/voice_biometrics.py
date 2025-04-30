import librosa
import numpy as np
from sklearn.mixture import GaussianMixture
import os
import pickle
import json
from services.user_service import get_user_by_id

# Path to store voice prints
VOICE_PRINTS_DIR = os.path.join(os.path.dirname(__file__), '../data/voice_prints')
os.makedirs(VOICE_PRINTS_DIR, exist_ok=True)

def extract_voice_features(audio_path):
    """
    Extract MFCC features from an audio file for voice biometrics.
    """
    # Load the audio file
    y, sr = librosa.load(audio_path, sr=None)
    
    # Extract MFCCs (Mel-Frequency Cepstral Coefficients)
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    
    # Normalize features
    mfccs = (mfccs - np.mean(mfccs, axis=1, keepdims=True)) / np.std(mfccs, axis=1, keepdims=True)
    
    return mfccs.T  # Transpose for sklearn compatibility

def get_voice_print_path(user_id):
    """Get the path to a user's voice print file."""
    return os.path.join(VOICE_PRINTS_DIR, f"user_{user_id}_voiceprint.pkl")

def enroll_user_voice(audio_path, user_id):
    """
    Enroll a new user by creating a voice print from their audio sample.
    In a real system, multiple samples would be used.
    """
    features = extract_voice_features(audio_path)
    
    # Train a Gaussian Mixture Model on the user's voice
    gmm = GaussianMixture(n_components=16, covariance_type='diag', max_iter=200)
    gmm.fit(features)
    
    # Save the model
    with open(get_voice_print_path(user_id), 'wb') as f:
        pickle.dump(gmm, f)
    
    return {'success': True, 'message': 'Voice enrolled successfully'}

def authenticate_voice(audio_path, user_id, threshold=None):
    """
    Authenticate a user based on their voice.
    Returns True if authenticated, False otherwise.
    
    In a POC, this is simplified. A real system would:
    - Have more sophisticated models
    - Use multiple enrollment samples
    - Have better thresholding
    - Include anti-spoofing measures
    """
    # Check if we have a voice print for this user
    voice_print_path = get_voice_print_path(user_id)
    
    if not os.path.exists(voice_print_path):
        # For demo purposes, if no voice print exists, create one
        # In a real system, this would return an error
        return enroll_user_voice(audio_path, user_id)
    
    # Load the user's voice model
    try:
        with open(voice_print_path, 'rb') as f:
            gmm = pickle.load(f)
    except (pickle.PickleError, IOError) as e:
        return {
            'authenticated': False,
            'error': f"Error loading voice model: {str(e)}",
            'user_id': user_id
        }
    
    # Extract features from the provided audio
    try:
        features = extract_voice_features(audio_path)
    except Exception as e:
        return {
            'authenticated': False,
            'error': f"Error extracting voice features: {str(e)}",
            'user_id': user_id
        }
    
    # Calculate log likelihood
    score = gmm.score(features)
    
    # Use adaptive thresholding - for demo we're setting a very permissive threshold
    if threshold is None:
        # This is very permissive for the POC, adjust based on your testing
        threshold = -80  # Default value based on typical log-likelihood scores
    
    authenticated = score > threshold
    
    return {
        'authenticated': authenticated,
        'confidence': score,
        'threshold': threshold,
        'user_id': user_id
    }
