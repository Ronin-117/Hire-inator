from humanize_ai_text import HumanizedAI
from dotenv import load_dotenv
import os


text="""
Emergent behavior is one of the most fascinating and widely applicable concepts in both natural and artificial systems.
"""

load_dotenv()
HUMANIZED_AI = os.environ.get("HUMANIZED_AI")
humanizer = HumanizedAI(api_key=HUMANIZED_AI)

try:
    result = humanizer.run(text)
    print(result['humanizedText'])
except Exception as e:
    print(f"An error occurred: {str(e)}")

