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
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime
import subprocess # For running external commands
import os         # For path manipulation
import tempfile   # For creating temporary directories

from transformer.app import AcademicTextHumanizer
import re


humanizer = AcademicTextHumanizer(p_passive=0.3, p_synonym_replacement=0.3, p_academic_transition=0.4)
gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

class ContentChunk(BaseModel):
    """Schema for a single passage of generated content."""
    title: str = Field(description="A unique key for the placeholder (e.g., 'summary_section', 'experience_tech_solutions').")
    content: str = Field(description="The generated text content for this section.")

class TailoredResumeResponse(BaseModel):
    """
    Schema for the main Gemini response, containing both the template
    and the content chunks to be inserted.
    """
    latex_template: str = Field(description="The full LaTeX document with f-string like placeholders (e.g., {summary_section}).")
    content_chunks: List[ContentChunk] = Field(description="A list of all the content chunks to be humanized and inserted into the template.")

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
            for i in range(1):
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
    
def get_tailored_template_and_chunks(base_latex, job_desc, instructions):
    # This function is mostly the same as your script
    print("\n🤖 Sending request to Gemini for template and content generation...")
    prompt = f"""
    You are an expert resume editor. Your task is to update the 'BASE LATEX RESUME' based on the provided 'JOB DESCRIPTION' and 'USER INSTRUCTIONS'.Try to make the content in the resume more human like(dont need to use complex language , just simple english).
    make the entire resume fit in one page (only add details that are relevent to the JOB DESCRIPTION if need). try to maintain the formating of the BASE LATEX

    **CRITICAL INSTRUCTIONS:**
    1.  **PRESERVE PERSONAL DETAILS:** You MUST preserve all personal details from the base resume (Name, Contact, Education, etc.). DO NOT replace them with generic information.
    2.  **ADAPT, DO NOT REPLACE:** Adapt the phrasing of the Summary and Experience sections to match the job description. Do not write a new resume from scratch.
    3.  **MAINTAIN STRUCTURE:** The output `latex_template` must maintain the exact LaTeX structure and commands of the original.
    4.  **ESCAPE SPECIAL CHARACTERS:** This is crucial for the final document to compile. Within the generated text content, you MUST escape any special LaTeX characters. For example, a hash symbol '#' MUST be written as `\#`. An ampersand '&' MUST be written as `\&`. A percentage sign '%' MUST be written as `\%`.
    5.  **BOLD LABELS:** Fix this LaTeX code by properly formatting bold labels in list items and correcting any character issues that might cause compilation errors. Ensure each label is bolded cleanly and any problematic symbols are handled safely for LaTeX.
    6.  **LIST FORMATING** Ensure all bullet points are wrapped inside the correct LaTeX list environments using begin and end blocks like beginitemize and enditemize with itemize in curly backets, with each entry starting with item.
    7. **PDF COMPILATION SAFETY:** Your output must be clean and compile without LaTeX errors. This means avoiding unescaped characters, broken lists, or malformed sectioning commands.

    Your response MUST be in two parts:
    1.  `latex_template`: A complete LaTeX document that preserves the original structure and formatting. For any long-form text or paragraph (like a summary or a job description bullet point), you MUST replace the text with a unique placeholder in the format `{{placeholder_key}}`. For example, `\section*{{Summary}} \n {{summary_section}}`. The bullet points for each job experience should be rewritten to sound natural and human, tailored to the job description.
    2.  `content_chunks`: A list of JSON objects. Each object must contain two keys: `title` (the exact `placeholder_key` used in the template) and `content` (the detailed, AI-generated paragraph or text that should go into that placeholder).

    --- BASE LATEX RESUME ---
    {base_latex}

    --- JOB DESCRIPTION ---
    {job_desc}

    --- USER INSTRUCTIONS ---
    {instructions}
    """
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config={"response_mime_type": "application/json", "response_schema": TailoredResumeResponse},
        )
        return response.parsed
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return None

def humanize_content_chunks(chunks: List[ContentChunk]) -> Dict[str, str]:
    print("\n⚙️ Running humanization process on all chunks...")
    humanized_map = {}
    special_chars = ['#', '$', '%', '&', '_', '{', '}']
    for chunk in chunks:
        # Replace this line with a real humanizer call if you get one working later
        humanized_text = humanizer.humanize_text(
                            chunk.content,
                            use_passive=True,
                            use_synonyms=True
                        )
        for char in special_chars:
            broken_escape = f'\\ {char}'   # e.g., looks for '\ #'
            correct_escape = f'\\{char}'    # e.g., should be '\#'
            if broken_escape in humanized_text:
                humanized_text = humanized_text.replace(broken_escape, correct_escape)
        humanized_map[chunk.title] = humanized_text
        print(f"  - Humanized '{chunk.title}'")
    
    print("✅ Dummy humanization complete.")
    return humanized_map

def populate_template(template: str, content_map: Dict[str, str]) -> str:
    # This function is the same as your working script
    print("\n🧩 Stitching humanized content into the final template...")
    
    final_latex = template
    
    # Loop through the map of content we need to insert
    for placeholder_key, content in content_map.items():
        # Create the placeholder format, e.g., "{summary_section}"
        placeholder_to_find = "{" + placeholder_key + "}"
        
        if placeholder_to_find in final_latex:
            # Directly replace the placeholder with the content
            final_latex = final_latex.replace(placeholder_to_find, content)
        else:
            # This is an important warning for debugging
            print(f"⚠️ WARNING: Placeholder '{placeholder_to_find}' not found in the template. Skipping.")
            
    print("✅ Stitching complete.")
    return final_latex

@csrf_exempt
@firebase_auth_required
def tailor_resume_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    user_uid = request.user_id
    db = firestore.client()
    
    # Get inputs from the frontend request
    base_resume_id = request.POST.get('base_resume_id')
    job_description = request.POST.get('job_description')

    if not base_resume_id or not job_description:
        return JsonResponse({'error': 'base_resume_id and job_description are required.'}, status=400)

    try:
        # 1. Fetch base resume and user instructions from Firestore
        print("Fetching data from Firestore...")
        resume_ref = db.collection('resumes').document(base_resume_id)
        base_resume_doc = resume_ref.get()
        if not base_resume_doc.exists or base_resume_doc.to_dict().get('userId') != user_uid:
            return JsonResponse({'error': 'Base resume not found or permission denied.'}, status=404)
        
        user_ref = db.collection('users').document(user_uid)
        user_doc = user_ref.get()
        
        base_latex = base_resume_doc.to_dict().get('latexContent', '')
        user_instructions = user_doc.to_dict().get('customInstructions', '')

        print("-" * 20)
        print(f"DEBUG: Sending Base LaTeX to Gemini (first 200 chars): \n{base_latex[:200]}...")
        print("-" * 20)

        # 2. Run the full AI + Humanize + Stitch process
        tailored_response = get_tailored_template_and_chunks(base_latex, job_description, user_instructions)
        if not tailored_response:
            raise Exception("Failed to get response from Gemini.")
            
        humanized_map = humanize_content_chunks(tailored_response.content_chunks)
        final_latex = populate_template(tailored_response.latex_template, humanized_map)
        
        # 3. Save the result as a NEW resume in Firestore
        print("Saving tailored resume to Firestore...")
        new_resume_data = {
            'userId': user_uid,
            'resumeName': f"Tailored for: {base_resume_doc.to_dict().get('resumeName', 'Untitled')}",
            'latexContent': final_latex,
            'isDraft': True, # We can use a flag to distinguish drafts
            'createdAt': firestore.SERVER_TIMESTAMP,
            'lastUpdated': firestore.SERVER_TIMESTAMP,
            'jobDescription': job_description, 
        }
        new_doc_ref = db.collection('resumes').add(new_resume_data)
        new_resume_id = new_doc_ref[1].id
        
        # 4. Return the ID of the new draft resume
        return JsonResponse({
            'status': 'success', 
            'message': 'Resume tailored successfully!',
            'newResumeId': new_resume_id
        })

    except Exception as e:
        print(f"An error occurred during tailoring: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@firebase_auth_required
def get_resume_details_view(request, resume_id: str):
    """Fetches the current data of a single resume document."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method is allowed'}, status=405)

    user_uid = request.user_id
    db = firestore.client()

    try:
        resume_ref = db.collection('resumes').document(resume_id)
        resume_doc = resume_ref.get()

        if not resume_doc.exists:
            return JsonResponse({'error': 'Resume not found'}, status=404)

        resume_data = resume_doc.to_dict()

        # Security Check: Ensure the user owns this resume
        if resume_data.get('userId') != user_uid:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Return all the data
        return JsonResponse(resume_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
@firebase_auth_required
def refine_resume_view(request, resume_id: str):
    """Takes a new instruction and re-runs the AI pipeline on an existing resume."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    user_uid = request.user_id
    db = firestore.client()

    # Get the new instruction from the request
    new_instruction = request.POST.get('instruction')
    job_description = request.POST.get('job_description') # We might need this for context

    if not new_instruction:
        return JsonResponse({'error': 'An instruction is required.'}, status=400)

    try:
        # 1. Fetch the CURRENT resume document and user instructions
        resume_ref = db.collection('resumes').document(resume_id)
        base_resume_doc = resume_ref.get()
        if not base_resume_doc.exists or base_resume_doc.to_dict().get('userId') != user_uid:
            return JsonResponse({'error': 'Resume not found or permission denied.'}, status=404)
        
        user_ref = db.collection('users').document(user_uid)
        user_doc = user_ref.get()

        current_latex = base_resume_doc.to_dict().get('latexContent', '')
        # Combine saved instructions with the new one for better context
        base_instructions = user_doc.to_dict().get('customInstructions', '')
        combined_instructions = f"{base_instructions}\n\nFurther refinement: {new_instruction}"
        
        # 2. Run the full AI pipeline again with the new instruction
        tailored_response = get_tailored_template_and_chunks(current_latex, job_description, combined_instructions)
        if not tailored_response:
            raise Exception("Failed to get response from Gemini during refinement.")
        
        humanized_map = humanize_content_chunks(tailored_response.content_chunks)
        refined_latex = populate_template(tailored_response.latex_template, humanized_map)

        # 3. UPDATE the existing document in Firestore
        print(f"Updating resume {resume_id} in Firestore...")
        resume_ref.update({
            'latexContent': refined_latex,
            'lastUpdated': firestore.SERVER_TIMESTAMP,
        })

        # 4. Return the newly generated LaTeX content
        return JsonResponse({
            'status': 'success',
            'message': 'Resume refined successfully!',
            'newLatexContent': refined_latex
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
@firebase_auth_required
def delete_resume_view(request, resume_id: str):
    # This view should only respond to DELETE requests for correctness
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Only DELETE method is allowed'}, status=405)

    user_uid = request.user_id
    db = firestore.client()

    try:
        resume_ref = db.collection('resumes').document(resume_id)
        resume_doc = resume_ref.get()

        if not resume_doc.exists:
            # It's good practice to return 404 if the resource doesn't exist
            return JsonResponse({'error': 'Resume not found'}, status=404)

        # CRITICAL SECURITY CHECK: Ensure the user owns this resume before deleting
        if resume_doc.to_dict().get('userId') != user_uid:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # If checks pass, delete the document
        resume_ref.delete()
        print(f"User {user_uid} deleted resume {resume_id}")
        
        return JsonResponse({'status': 'success', 'message': 'Resume deleted successfully.'})

    except Exception as e:
        print(f"An error occurred during resume deletion: {e}")
        return JsonResponse({'error': 'An internal server error occurred.'}, status=500)


@csrf_exempt
@firebase_auth_required
def download_resume_tex_view(request, resume_id: str):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method is allowed'}, status=405)

    user_uid = request.user_id
    db = firestore.client()

    try:
        resume_ref = db.collection('resumes').document(resume_id)
        resume_doc = resume_ref.get()

        if not resume_doc.exists:
            return JsonResponse({'error': 'Resume not found'}, status=404)

        resume_data = resume_doc.to_dict()

        # CRITICAL SECURITY CHECK: Ensure the user owns this resume
        if resume_data.get('userId') != user_uid:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        latex_content = resume_data.get('latexContent', '')
        resume_name = resume_data.get('resumeName', 'resume')

        # Create an HTTP response with the LaTeX content as plain text
        response = HttpResponse(latex_content, content_type='text/plain; charset=utf-8')
        
        # This header tells the browser to download the file with a .tex extension
        response['Content-Disposition'] = f'attachment; filename="{resume_name}.tex"'
        
        return response

    except Exception as e:
        print(f"An error occurred during TeX download: {e}")
        return JsonResponse({'error': 'An internal server error occurred.'}, status=500)