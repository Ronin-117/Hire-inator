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