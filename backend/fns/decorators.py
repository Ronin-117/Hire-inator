# fns/decorators.py

from functools import wraps
from django.http import JsonResponse
from firebase_admin import auth

def firebase_auth_required(f):
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        # 1. Get the token from the 'Authorization: Bearer <token>' header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authorization header missing or invalid'}, status=401)
        
        id_token = auth_header.split(' ').pop()

        try:
            # 2. Verify the token using the Firebase Admin SDK
            decoded_token = auth.verify_id_token(id_token)
            
            # 3. Add the decoded token (and user UID) to the request object
            #    so the view can access it.
            request.user_id = decoded_token['uid']
            request.firebase_user = decoded_token

        except auth.InvalidIdTokenError:
            return JsonResponse({'error': 'Invalid Firebase ID token'}, status=403)
        except auth.ExpiredIdTokenError:
            return JsonResponse({'error': 'Firebase ID token has expired'}, status=403)
        except Exception as e:
            # Handle other potential errors during verification
            return JsonResponse({'error': f'An error occurred during token verification: {e}'}, status=500)
        
        # 4. If token is valid, call the original view function
        return f(request, *args, **kwargs)
    
    return decorated_function