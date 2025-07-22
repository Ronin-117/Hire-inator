from humanize_ai_text import HumanizedAI
from dotenv import load_dotenv
import os


text="""
Artificial Intelligence (AI) refers to the ability of machines to perform tasks that typically require human intelligence. These tasks include understanding language, recognizing images, making decisions, and learning from experience. AI is used in everyday applications like voice assistants, recommendation systems, self-driving cars, and medical diagnostics. As AI continues to advance, it has the potential to greatly improve efficiency and solve complex problems—but it also raises important questions about ethics, privacy, and the future of work.
"""

load_dotenv()
HUMANIZED_AI = os.environ.get("HUMANIZED_AI")
humanizer = HumanizedAI(api_key=HUMANIZED_AI)

try:
    result = humanizer.run(text)
    print(result['humanizedText'])
except Exception as e:
    print(f"An error occurred: {str(e)}")