# fns/apps.py

from django.apps import AppConfig
import firebase_admin
from firebase_admin import credentials
import os
from django.conf import settings

class FnsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fns'

    def ready(self):
        # We still need to initialize Firebase for the admin SDK to work
        if not firebase_admin._apps:
            key_path = os.path.join(settings.BASE_DIR, 'serviceAccountKey.json')
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            print("🔥 Firebase App Initialized for Token Verification 🔥")
        try:
            print("🧠 Downloading NLTK resources for Humanizer...")
            from transformer.app import download_nltk_resources
            download_nltk_resources()
            print("✅ NLTK resources are ready.")
        except ImportError:
            print("⚠️ WARNING: 'transformer.app' library not found. Humanizer will not work.")
        except Exception as e:
            print(f"❌ ERROR downloading NLTK resources: {e}")