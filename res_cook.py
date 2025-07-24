from google import genai
from google.genai import types
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Define response schema
class Res(BaseModel):
    ai_response: str
    resume_tex: str

# Load the LaTeX resume file
def load_tex(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading .tex file: {e}")
        return ""

# Save LaTeX output if needed
def save_tex(file_path, content):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"Error saving .tex file: {e}")

# Load original resume
tex_path = "main.tex"
latex_content = load_tex(tex_path)
if not latex_content:
    print("Exiting due to missing or empty LaTeX file.")
    exit(1)

# Get job description once
job_description = "Data analyst at MathCo.inc"

# Initialize Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# Interaction loop
while True:
    user_instruction = input("\nYour instruction (or type 'exit' to quit): ").strip()
    if user_instruction.lower() == "exit":
        break

    # Build the prompt
    prompt = (
        f"Analyze the provided TeX resume and update it according to this instruction: {user_instruction}\n"
        "Instructions:\n"
        "- Keep the resume within a single page\n"
        "- Make it ATS-friendly\n"
        f"- Tailor it for the job description: {job_description}\n"
        f"here is the latex:{latex_content}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # ✅ Model unchanged
            contents=[
                prompt
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": Res,
            },
        )

        raw_text = response.text.strip()
        print("\n=== Raw JSON Response ===")
        print(raw_text)

        try:
            parsed = Res.parse_obj(json.loads(raw_text))
            latex_content = parsed.resume_tex

            print("\n=== Updated LaTeX Resume ===\n")
            print(latex_content)

            # Optional: save after each iteration
            save_tex("updated_resume.tex", latex_content)

        except Exception as parse_error:
            print(f"\nError parsing Gemini output: {parse_error}")
            print("Raw response was:")
            print(raw_text)

    except Exception as e:
        print(f"Error during Gemini call: {e}")
