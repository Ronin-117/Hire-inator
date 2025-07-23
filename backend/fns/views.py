from django.shortcuts import render

# Create your views here.
# fns/views.py

from django.http import HttpResponse, JsonResponse
from firebase_admin import firestore # Import firestore
from .decorators import firebase_auth_required

def home(request):
    return HttpResponse("<h1>Welcome! Go to /test-firebase to write to the database.</h1>")

# Our new test view
def test_firebase_connection(request):
    try:
        # Get a reference to the Firestore client
        db = firestore.client()

        # Create a new document in a collection called 'test_collection'
        doc_ref = db.collection('test_logs').document('log_from_django')
        doc_ref.set({
            'message': 'Hello from Django!',
            'status': 'success'
        })

        return JsonResponse({"status": "success", "message": "Data written to Firestore successfully!"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
    
@firebase_auth_required
def get_user_profile(request):
    """
    This view can only be accessed by users who provide a valid
    Firebase ID token.
    """
    # Thanks to our decorator, we can safely access the user's UID
    user_uid = request.user_id 
    
    print(f"Authenticated user with UID: {user_uid}")

    # In a real app, you would now fetch data from Firestore for this user
    # For example: db.collection('users').document(user_uid).get()
    
    return JsonResponse({
        "status": "success",
        "message": f"You have accessed a protected endpoint. Your Firebase UID is: {user_uid}",
        # We can also return the full token data for debugging
        "user_data": request.firebase_user 
    })