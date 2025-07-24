from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
# fns/views.py

from django.http import HttpResponse, JsonResponse
from firebase_admin import firestore # Import firestore
from .decorators import firebase_auth_required

# Imports for Gemini
from google import genai
from google.genai import types
from pydantic import BaseModel
from datetime import datetime
import subprocess # For running external commands
import os         # For path manipulation
import tempfile   # For creating temporary directories

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


def convert_pdf_to_latex(pdf_bytes):
    """
    Converts PDF bytes to a LaTeX string using the Gemini API,
    following the original working script's logic.
    """
    # This is your Pydantic model for the response structure
    class Res(BaseModel):
        ai_response: str
        resume_tex: str

    # --- THE FIX ---
    # The incorrect 'genai.configure(...)' line has been removed.
    # We now initialize the client directly with the API key,
    # just like in your working standalone script.
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    prompt = (
        "Analyze the provided PDF resume and convert it into a complete, single, and compilable "
        "LaTeX document. \n\n"
        "Instructions:\n"
        "1. Use the 'article' document class.\n"
        "2. Use the 'geometry' package for appropriate margins (e.g., `\\usepackage[a4paper, margin=1in]{geometry}`).\n"
        "3. Preserve the sections, layout, and text formatting (like bold or itemized lists) as closely as possible.\n"
        "4. The entire output in the 'resume_tex' field must be a single raw string of LaTeX code, "
        "starting with `\\documentclass` and ending with `\\end{document}`."
    )

    # This is the exact, working API call from your original script
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf'),
            prompt
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": Res,
        },
    )
    
    parsed_response: Res = response.parsed
    return parsed_response.resume_tex


# --- The Django View (No changes needed here) ---
@csrf_exempt
@firebase_auth_required
def upload_resume_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    if 'resume_pdf' not in request.FILES:
        return JsonResponse({'error': 'No PDF file found in request'}, status=400)

    uploaded_file = request.FILES['resume_pdf']
    user_uid = request.user_id

     # STEP 2: Get the custom resume name from the POST data.
    # request.POST contains text data sent along with files in FormData.
    resume_name = request.POST.get('resume_name', '').strip()

    # STEP 3: If the name is empty, create a default one.
    if not resume_name:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        resume_name = f"Resume {timestamp}"

    try:
        print(f"Processing '{uploaded_file.name}' for user {user_uid}...")
        pdf_bytes = uploaded_file.read()
        
        print("Sending to Gemini for conversion...")
        latex_code = convert_pdf_to_latex(pdf_bytes)
        print("Conversion successful.")

        print("Saving to Firestore...")
        db = firestore.client()
        resume_data = {
            'userId': user_uid,
            'resumeName': resume_name, 
            'originalFilename': uploaded_file.name,
            'latexContent': latex_code,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'lastUpdated': firestore.SERVER_TIMESTAMP,
        }
        
        doc_ref = db.collection('resumes').add(resume_data)
        
        print(f"Resume saved with ID: {doc_ref[1].id}")

        return JsonResponse({
            'status': 'success', 
            'message': 'Resume converted and saved successfully!',
            'resumeId': doc_ref[1].id
        })

    except Exception as e:
        print(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@firebase_auth_required
def upload_tex_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    if 'resume_tex' not in request.FILES:
        return JsonResponse({'error': 'No .tex file found in request'}, status=400)

    uploaded_file = request.FILES['resume_tex']
    user_uid = request.user_id
    
    # Use the same logic for getting the custom name
    resume_name = request.POST.get('resume_name', '').strip()
    if not resume_name:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        resume_name = f"Imported Resume {timestamp}"

    try:
        # Read the content of the .tex file. It's bytes, so we decode it.
        latex_content = uploaded_file.read().decode('utf-8')

        print(f"Saving uploaded .tex file to Firestore with name: '{resume_name}'")
        db = firestore.client()
        
        resume_data = {
            'userId': user_uid,
            'resumeName': resume_name,
            'originalFilename': uploaded_file.name,
            'latexContent': latex_content,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'lastUpdated': firestore.SERVER_TIMESTAMP,
        }
        
        doc_ref = db.collection('resumes').add(resume_data)
        
        return JsonResponse({
            'status': 'success', 
            'message': 'TeX file saved successfully!',
            'resumeId': doc_ref[1].id
        })

    except UnicodeDecodeError:
        return JsonResponse({'error': 'Could not read the file. Please ensure it is a valid UTF-8 encoded text file.'}, status=400)
    except Exception as e:
        print(f"An error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    
# --- ADD THIS NEW HELPER FUNCTION ---
def compile_latex_to_pdf_bytes(latex_content: str):
    """
    Takes a string of LaTeX content, compiles it in a temporary directory,
    and returns the binary content of the resulting PDF.
    Returns None if compilation fails.
    """
    # Create a temporary directory that will be automatically cleaned up
    with tempfile.TemporaryDirectory() as tempdir:
        tex_filename = "resume.tex"
        tex_filepath = os.path.join(tempdir, tex_filename)
        pdf_filepath = os.path.join(tempdir, "resume.pdf")

        # 1. Write the LaTeX content to the .tex file
        with open(tex_filepath, "w", encoding="utf-8") as f:
            f.write(latex_content)

        # 2. The command to run pdflatex
        command = [
            "pdflatex",
            "-interaction=nonstopmode",
            f"-output-directory={tempdir}", # Ensure output is in the same temp dir
            tex_filepath,
        ]

        try:
            # 3. Run the compiler command. We run it twice for complex docs (e.g., table of contents)
            # which is good practice.
            for i in range(2):
                print(f"Running pdflatex pass {i+1}...")
                subprocess.run(command, check=True, capture_output=True, text=True)

            # 4. If compilation was successful, read the PDF bytes
            if os.path.exists(pdf_filepath):
                with open(pdf_filepath, "rb") as f:
                    pdf_bytes = f.read()
                print("PDF compilation successful.")
                return pdf_bytes
            else:
                return None

        except subprocess.CalledProcessError as e:
            print(f"❌ PDF Compilation Failed!")
            print(e.stdout) # Print the LaTeX log for debugging
            return None
        
@csrf_exempt
@firebase_auth_required
def download_resume_pdf_view(request, resume_id: str):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method is allowed'}, status=405)

    user_uid = request.user_id
    db = firestore.client()

    try:
        # 1. Fetch the resume document from Firestore
        resume_ref = db.collection('resumes').document(resume_id)
        resume_doc = resume_ref.get()

        if not resume_doc.exists:
            return JsonResponse({'error': 'Resume not found'}, status=404)

        resume_data = resume_doc.to_dict()

        # 2. SECURITY CHECK: Ensure the user owns this resume
        if resume_data.get('userId') != user_uid:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        # 3. Get the LaTeX content and compile it
        latex_content = resume_data.get('latexContent')
        pdf_bytes = compile_latex_to_pdf_bytes(latex_content)

        if pdf_bytes:
            # 4. If compilation is successful, create the HTTP response
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            # This header tells the browser to download the file
            response['Content-Disposition'] = f'attachment; filename="{resume_data.get("resumeName", "resume")}.pdf"'
            return response
        else:
            return JsonResponse({'error': 'Failed to compile LaTeX into PDF.'}, status=500)

    except Exception as e:
        print(f"An error occurred during PDF download: {e}")
        return JsonResponse({'error': 'An internal server error occurred.'}, status=500)