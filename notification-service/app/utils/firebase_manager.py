import firebase_admin
from firebase_admin import credentials
import os
import json
import logging

logger = logging.getLogger("FirebaseManager")

def init_firebase():
    """
    Initialize Firebase Admin SDK using credentials from environment variable.
    Expected Env Var: FIREBASE_KEY (content of service-account.json)
    """
    try:
        # Check if already initialized
        if firebase_admin._apps:
            return True

        firebase_key = os.environ.get('FIREBASE_KEY')
        if not firebase_key:
            logger.warning("FIREBASE_KEY environment variable not found.")
            return False

        # Parse JSON
        cred_dict = json.loads(firebase_key)
        
        # Initialize
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin initialized successfully from Environment Variable.")
        return True
    
    except json.JSONDecodeError:
        logger.error("Failed to parse FIREBASE_KEY JSON.")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return False

def get_firebase_status():
    """Returns the current status of Firebase connection."""
    if firebase_admin._apps:
        return "Connected"
    
    if os.environ.get('FIREBASE_KEY'):
        return "Configured (Trying to Connect)"
    
    return "Missing Configuration"
