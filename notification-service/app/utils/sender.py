import json
import secrets
from ..models import db, Notification

def process_and_send_notification(title, body, target='all', api_key_id=None):
    """
    Core logic to send a notification (e.g. via Firebase) and save the record.
    Currently simulates the "Successfully Sent" response.
    """
    
    # 1. SEND via Firebase (Placeholder for actual FCM code)
    # In a real app:
    # response = firebase_messaging.send(Message(...))
    
    # Simulated Response
    simulated_response = {
        'message_id': secrets.token_hex(8),
        'success': True,
        'provider': 'Firebase Cloud Messaging'
    }
    
    # 2. SAVE to Database
    try:
        new_notif = Notification(
            title=title, 
            body=body, 
            target=target,
            status='success' if simulated_response['success'] else 'failed',
            response=json.dumps(simulated_response),
            api_key_id=api_key_id
        )
        db.session.add(new_notif)
        db.session.commit()
        return True, "Notification queued and saved."
    except Exception as e:
        db.session.rollback()
        return False, str(e)
