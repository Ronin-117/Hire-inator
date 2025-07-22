# --- IMPORTS ---
from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import pathlib

# --- SETUP ---
# Load environment variables (for the API key)
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Check if the API key is available
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file or as an environment variable.")

# Define the input PDF and the desired output .tex file
input_filepath = pathlib.Path("Resume12-07-25.pdf")
output_filename = "resume_from_gemini.tex"

# --- REFINED PROMPT ---
# This prompt is more specific to guide the model towards a better result.
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


# --- DEFINE THE RESPONSE STRUCTURE (Your original class) ---
class Res(BaseModel):
    ai_response: str
    resume_tex: str


# --- MAIN LOGIC ---
try:
    print(f"1. Reading PDF file: '{input_filepath}'...")
    # Check if the PDF file exists before proceeding
    if not input_filepath.exists():
        raise FileNotFoundError(f"The input file was not found at: {input_filepath}")
    
    pdf_bytes = input_filepath.read_bytes()

    # --- INITIALIZE THE CLIENT ---
    client = genai.Client(api_key=GEMINI_API_KEY)

    # --- CALL THE GEMINI API (Your original, working call) ---
    print("2. Sending request to Gemini API... (This may take a moment)")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
          types.Part.from_bytes(
            data=pdf_bytes,
            mime_type='application/pdf',
          ),
          prompt
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": Res,
        },
    )

    # --- PROCESS THE RESPONSE ---
    print("3. Processing the response from Gemini...")
    # Get the instantiated Pydantic object from the response
    parsed_response: Res = response.parsed
    
    # Extract the raw LaTeX code from the object
    latex_code_from_gemini = parsed_response.resume_tex
    
    # --- THIS IS THE NEW PART: SAVE THE FILE ---
    print(f"4. Saving the LaTeX code to '{output_filename}'...")
    # Use 'w' mode to write the file, and specify utf-8 encoding for safety
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(latex_code_from_gemini)
    
    print("\n✅ Success! The file has been saved.")
    print(f"You can now try to compile '{output_filename}' using pdflatex.")

except Exception as e:
    print(f"\n❌ An error occurred: {e}")