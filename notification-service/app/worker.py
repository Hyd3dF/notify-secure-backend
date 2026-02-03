import threading
import time
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BackgroundWorker")

class BackgroundWorker(threading.Thread):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.daemon = True # Daemon thread exits when main program exits
        self.running = True

    def run(self):
        """Main loop of the worker."""
        logger.info("Background Worker Started")
        
        while self.running:
            try:
                # Need application context to access DB if needed
                with self.app.app_context():
                    self.check_database()
            except Exception as e:
                logger.error(f"Error in background worker: {e}")
            
            # Sleep interval (configurable)
            time.sleep(5) 

    def check_database(self):
        """Logic to check external DB and send notifications."""
        # Check if PocketBase is configured
        pb_url = os.environ.get('POCKETBASE_URL') # e.g., http://127.0.0.1:8090
        
        if not pb_url:
            # Silent return if not configured to avoid log spam
            return

        try:
            from pocketbase import PocketBase
            client = PocketBase(pb_url)
            
            # Authenticate as Admin (Required for Realtime restrictions often)
            admin_email = os.environ.get('POCKETBASE_ADMIN_EMAIL')
            admin_pass = os.environ.get('POCKETBASE_ADMIN_PASSWORD')
            
            if admin_email and admin_pass:
                try:
                    client.admins.auth_with_password(admin_email, admin_pass)
                    logger.info("PocketBase Admin Authentication Successful")
                except Exception as auth_error:
                    logger.error(f"PocketBase Admin Auth Failed: {auth_error}")
                    return # Stop if auth fails
            else:
                logger.warning("No PocketBase Admin credentials found. Attempting guest access...")

            logger.info(f"Connecting to PocketBase at {pb_url}...")
            
            def on_record_create(data):
                action = data.action
                record = data.record
                
                if action == 'create':
                    def get_field(rec, *keys):
                        for key in keys:
                            if isinstance(rec, dict) and key in rec:
                                return rec.get(key)
                            if hasattr(rec, key):
                                return getattr(rec, key)
                        return None

                    record_id = get_field(record, 'id') or 'unknown'
                    logger.info(f"New message detected: {record_id}")
                    # Extract Data (support both legacy and current field names)
                    title = get_field(record, 'title', 'subject')
                    body = get_field(record, 'body', 'content', 'message')
                    target = get_field(record, 'target') or 'all'

                    if not title or not body:
                        logger.warning(
                            "Skipping message %s due to missing fields (title=%s, body=%s).",
                            record_id,
                            title,
                            body
                        )
                        return
                    
                    # Process inside App Context
                    with self.app.app_context():
                        from .utils.sender import process_and_send_notification
                        process_and_send_notification(title, body, target)
                        
            # Subscribe to 'messages' collection
            # This is a blocking call in some SDK versions or runs in thread.
            # Ideally we want this to be persistent. The Python SDK 'subscribe' might be non-blocking or blocking.
            # Verification needed: standard python SDK relies on SSE.
            
            client.collection('messages').subscribe(on_record_create)
            
            # Keep thread alive to listen
            while self.running:
                time.sleep(1)
                
        except ImportError:
            logger.error("PocketBase SDK not installed. Run 'pip install pocketbase'.")
        except Exception as e:
            logger.error(f"PocketBase Connection Error: {e}")
            # Wait a bit before retrying connection
            time.sleep(10)
