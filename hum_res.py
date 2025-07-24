# File: process_resume_chunked.py

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from humanize_ai_text import HumanizedAI

# --- 1. SETUP AND CONFIGURATION ---
print("🚀 Initializing...")
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
HUMANIZED_AI_KEY = os.environ.get("HUMANIZED_AI")

if not GEMINI_API_KEY or not HUMANIZED_AI_KEY:
    raise ValueError("API keys for Gemini and HumanizedAI must be set in the .env file.")

# Initialize clients for both services
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
humanizer = HumanizedAI(api_key=HUMANIZED_AI_KEY)

# --- 2. PYDANTIC MODELS FOR STRUCTURED GEMINI RESPONSES ---

class TailoredResume(BaseModel):
    """Schema for the tailored resume response."""
    updated_latex: str

class TextChunk(BaseModel):
    """Schema for a single text chunk."""
    section_title: str = Field(description="The title of the section (e.g., 'Summary', 'Experience').")
    section_content: str = Field(description="The raw text content of that section.")

class ExtractedTextChunks(BaseModel):
    """Schema for the list of all chunks."""
    resume_chunks: List[TextChunk]

class StitchedResume(BaseModel):
    """Schema for the re-integrated resume response."""
    final_latex: str

# --- 3. HELPER FUNCTIONS ---

def tailor_resume_with_gemini(base_latex, job_desc, instructions):
    """Uses Gemini to modify the LaTeX resume based on inputs."""
    print("\n🤖 Sending request to Gemini for tailoring...")
    prompt = f"""
    You are an expert resume editor. Update the Base LaTeX Resume based on the Job Description and User Instructions.
    Preserve the LaTeX structure. Only modify content to align with the role. Respond with the complete, updated LaTeX code.

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
            config={
                "response_mime_type": "application/json",
                "response_schema": TailoredResume,
            },
        )
        print("✅ Gemini tailoring complete.")
        return response.parsed.updated_latex
    except Exception as e:
        print(f"❌ Gemini Tailoring Error: {e}")
        return None

def extract_text_chunks(latex_content):
    """Uses Gemini to extract structured text chunks from LaTeX."""
    print("\n extracting structured text chunks from LaTeX...")
    prompt = f"""
    From the following LaTeX document, extract the human-readable text content, broken down by section.
    For each section (like Summary, Experience, Education), provide its title and its full text content.
    Ignore all LaTeX commands, environments, and document setup.
    Present the result as a list of JSON objects, each with a 'section_title' and a 'section_content' key.

    --- LATEX DOCUMENT ---
    {latex_content}
    """
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config={
                "response_mime_type": "application/json",
                "response_schema": ExtractedTextChunks,
            },
        )
        print("✅ Text chunk extraction complete.")
        return response.parsed.resume_chunks
    except Exception as e:
        print(f"❌ Text Chunk Extraction Error: {e}")
        return None

def humanize_text(text_to_humanize):
    """Runs the text through the HumanizedAI service."""
    print(f"🗣️ Sending chunk to HumanizeAI (length: {len(text_to_humanize)} chars)...")
    try:
        result = humanizer.run(text_to_humanize)
        print("✅ Humanization of chunk complete.")
        return result['humanizedText']
    except Exception as e:
        print(f"❌ HumanizeAI Error: {e}")
        return None

def reintegrate_chunks_with_gemini(original_latex, humanized_chunks: List[TextChunk]):
    """Uses Gemini to put the humanized chunks back into the LaTeX structure."""
    print("\n🧩 Sending request to Gemini for chunk re-integration...")
    
    humanized_content_str = ""
    for chunk in humanized_chunks:
        humanized_content_str += f"--- SECTION: {chunk.section_title} ---\n{chunk.section_content}\n\n"

    prompt = f"""
    You are a precise text-stitching tool. Your task is to take an original LaTeX document and a series of humanized text chunks, identified by section titles. You must replace the content within each corresponding section of the LaTeX structure with the new humanized text.

    CRITICAL RULE: Do NOT add, remove, or generate any new content. Do NOT change the LaTeX commands or structure. Simply replace the original text sections with their corresponding humanized versions.

    --- ORIGINAL LATEX STRUCTURE ---
    {original_latex}

    --- HUMANIZED TEXT CHUNKS ---
    {humanized_content_str}
    
    --- FINAL STITCHED LATEX DOCUMENT ---
    """
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config={
                "response_mime_type": "application/json",
                "response_schema": StitchedResume,
            },
        )
        print("✅ Re-integration complete.")
        return response.parsed.final_latex
    except Exception as e:
        print(f"❌ Gemini Re-integration Error: {e}")
        return None

# --- 4. SAMPLE DATA ---
BASE_RESUME_LATEX = r"""
\documentclass[letterpaper,10pt]{article}

\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{xcolor}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage[default]{sourcesanspro}
\usepackage[T1]{fontenc}
\usepackage{tabularx}
\usepackage{graphicx}
\usepackage{ragged2e}

% ------ RESUME STYLING ------
\pagestyle{empty}

% Adjust margins for one-page fit
\addtolength{\oddsidemargin}{-0.6in}
\addtolength{\evensidemargin}{-0.6in}
\addtolength{\textwidth}{1.2in}
\addtolength{\topmargin}{-0.6in}
\addtolength{\textheight}{1.2in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Section formatting
\titleformat{\section}{
  \vspace{-10pt}\scshape\Large\raggedright
}{}{0em}{}[\color{black}\titlerule\vspace{-5pt}]

% Custom commands for resume structure
\newcommand{\resumeItem}[1]{\item\small{#1\vspace{-2pt}}}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & \textit{\small#2} \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-5pt}
}

% Command for Projects: {Title}{URL}{Tech Stack}
\newcommand{\resumeProjectHeading}[3]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textbf{#1} \href{#2}{\small[GitHub]} & \textit{\small#3} \\
    \end{tabular*}\vspace{-2pt}
}

% List environments
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=0.15in, itemsep=-3pt, topsep=0pt]}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

% Hyperlink setup
\hypersetup{
    colorlinks,
    linkcolor={blue!60!black},
    citecolor={blue!60!black},
    urlcolor={blue!60!black}
}

% Horizontal line for header
\newcommand{\linkline}{\noindent\makebox[\linewidth]{\color{black}\hrulefill}}

% ------ DOCUMENT START ------
\begin{document}

% --- HEADER ---
\begin{center}
    {\Huge \scshape \textbf{NEIL JOSEPH}} \\ \vspace{5pt}
    \linkline \\ \vspace{4pt}
    \small Kerala, India $|$ +91 9846604053 $|$ \href{mailto:neiljoseph0117@gmail.com}{\texttt{neiljoseph0117@gmail.com}} $|$ \href{https://www.linkedin.com/in/neil--joseph/}{LinkedIn} $|$ \href{https://github.com/Ronin-117}{GitHub} \\ \vspace{4pt}
    \linkline
\end{center}

% --- SUMMARY ---
\begin{center}
    \begin{tabular*}{\textwidth}{@{}p{\textwidth}@{
}}
    \small\justifying Highly analytical Computer Science undergraduate passionate about extracting insights from complex datasets to drive strategic business decisions. Proven ability to leverage data-driven solutions and machine learning techniques. Eager to apply strong technical and analytical skills as a Junior Data Analyst at mathco.inc, contributing to impactful data initiatives.
    \end{tabular*}
\end{center}


%----------- EDUCATION -----------
\section{Education}
\resumeSubHeadingListStart
    \resumeSubheading
    {Adi Shankara Institute of Engineering and Technology, Kalady}{2022 -- 2026}
    {B.Tech in Computer Science \& Engineering (Artificial Intelligence)}{CGPA: 9.0 / 10.0}
    \resumeSubheading
    {St. Sebastian's HSS, Palluruthy}{2020 -- 2022}
    {Higher Secondary Education (Computer Science)}{Percentage: 94.75\%}
\resumeSubHeadingListEnd

%----------- SKILLS -----------
\section{Core Competencies \& Technical Skills}
\begin{tabular*}{\textwidth}{@{}p{0.5\textwidth}p{0.5\textwidth}}
    \begin{itemize}[leftmargin=0.15in, label={$\bullet$}, itemsep=0pt]
        \item \textbf{Languages:} SQL, Python, C++, Java, C
        \item \textbf{AI/ML Frameworks:} TensorFlow, PyTorch, Scikit-learn
        \item \textbf{NLP \& CV Libraries:} LangChain, CrewAI, OpenCV, MediaPipe
        \item \textbf{Web Technologies:} Django, React.js, HTML, JavaScript
        \item\textbf{Cloud \& Developer Tools:} AWS, Git
    \end{itemize} &
    \begin{itemize}[leftmargin=0.15in, label={$\bullet$}, itemsep=0pt]
        \item \textbf{Analytical Problem-Solving}
        \item \textbf{Data-driven Decision Making}
        \item \textbf{Project Ownership \& Management}
        \item \textbf{Client-facing Communication}
    \end{itemize}
\end{tabular*}


%----------- EXPERIENCE -----------
\section{Experience}
\resumeSubHeadingListStart
    \resumeSubheading
    {Jorim Technology Solutions Pvt Ltd}{Chennai, TN}
    {AI Web Development Intern}{May 2025 -- July 2025}
    \resumeItemListStart
        \resumeItem{Led development of a data-driven, AI-integrated web application for healthcare, demonstrating end-to-end project ownership from data collection to deployment.}
        \resumeItem{Engineered scalable features using Django and React.js, facilitating data visualization and user interaction.}
    \resumeItemListEnd

    \resumeSubheading
    {InternsChoice}{Bengaluru, KA}
    {AI \& ML Intern}{Mar 2023 -- Apr 2023}
    \resumeItemListStart
        \resumeItem{Applied data analysis and machine learning techniques to derive insights and build practical business solutions, including an image classifier and customer service chatbot.}
        \resumeItem{Identified and automated key operational processes using data-driven AI solutions, enhancing efficiency.}
    \resumeItemListEnd
\resumeSubHeadingListEnd

%----------- PROJECTS -----------
\section{Projects}
\resumeSubHeadingListStart
    \resumeProjectHeading
        {CerebroMark: Automated Attendance Monitoring System}
        {https://github.com/Ronin-117/Automated_attendance}
        {Pytorch, OpenCV, Python}
    \resumeItemListStart
        \resumeItem{Developed a data-driven AI solution for automated classroom attendance (facial recognition), achieving \textbf{98.9\% accuracy} through robust data processing and model optimization.}
    \end{itemize}

    \resumeProjectHeading
        {GrindSensAI: AI-Based Physical Training \& Progress Tracker}
        {https://github.com/Ronin-117/GrindSensAI}
        {Django, React, MediaPipe}
    \resumeItemListStart
        \resumeItem{Built a data-driven fitness application leveraging computer vision to collect, analyze, and provide real-time form correction and progress tracking for \textbf{over 10 distinct exercises}, enabling personalized insights.}
    \end{itemize}

    \resumeProjectHeading
        {Oratis: AI-Powered Interview Preparation Platform}
        {https://github.com/Ronin-117/Mock_Online_InterviewAi}
        {NLP, Computer Vision, API}
    \resumeItemListStart
        \resumeItem{Developed an analytical tool for placement preparation, processing interview data to provide constructive performance feedback, featuring a 3D AI avatar for mock interviews.}
    \end{itemize}

    \resumeProjectHeading
        {Voxia: Sustainable Project Management Tool using IBM WatsonX}
        {https://github.com/Ronin-117/sustainability-tool}
        {IBM WatsonX, LangChain, API}
    \resumeItemListStart
        \resumeItem{Designed a proof-of-concept for the IBM watsonx challenge to help businesses assess project sustainability by analyzing relevant data, showcasing ability to leverage enterprise AI for GRC insights.}
    \end{itemize}

    \resumeProjectHeading
        {Custom AI Assistant with RAG}
        {https://github.com/Ronin-117/lang_chain_test}
        {LangChain, NLP, Python}
    \resumeItemListStart
        \resumeItem{Constructed a Retrieval-Augmented Generation (RAG) system to extract and synthesize accurate, context-aware answers from specialized knowledge bases, a core technique for data retrieval and analysis.}
    \end{itemize}
\resumeSubHeadingListEnd

%----------- ACHIEVEMENTS \& PUBLICATIONS -----------
\section{Achievements \& Publications}
\resumeSubHeadingListStart
    \resumeItem{\textbf{Secured Top 10 Finalist} position in IBM watsonx Challenge for "Voxia," an innovative sustainable project management tool.}
    \resumeItem{\textbf{Published Research Paper:} "Oratis: AI Guide to Ace interviews" - Co-authored paper presented at International Conference (April 2025).}
    \resumeItem{\textbf{Certifications:} AWS AI Cloud Practitioner (Udemy)[\href{https://drive.google.com/file/d/1hyq1dbVjAA1MLuaTsM54wPWLVKikRFmg/view?usp=sharing}{Certificate}], IBM watsonx.ai Technical Essentials (IBM)[\href{https://drive.google.com/file/d/1jE_tHyAmTK9e3APr32Q-aovg3wDvVlDL/view?usp=sharing}{Certificate}].}
\resumeSubHeadingListEnd

\end{document}
-------------------------
"""

JOB_DESCRIPTION = """
We are looking for a Senior Backend Engineer with a strong focus on cloud infrastructure and data pipelines. The ideal candidate will have over 5 years of experience with Python, AWS services (S3, Lambda, EC2), and building scalable data processing systems. Experience with Docker and Kubernetes is a major plus. The role involves designing and implementing backend services that support our machine learning models.
"""

# --- 5. MAIN APPLICATION FLOW ---
if __name__ == "__main__":
    
    # --- PHASE 1: TAILORING LOOP ---
    print("\n" + "="*50 + "\nPHASE 1: AI-POWERED RESUME TAILORING\n" + "="*50)
    current_latex = BASE_RESUME_LATEX
    while True:
        print("\n--- Current Resume ---\n" + current_latex + "\n" + "-"*22)
        user_instructions = input("Enter your instructions to tailor the resume (e.g., 'Emphasize cloud experience and AWS skills').\n> ")
        if not user_instructions:
            print("No instructions provided, using previous version.")
        
        tailored_latex = tailor_resume_with_gemini(current_latex, JOB_DESCRIPTION, user_instructions)
        
        if tailored_latex:
            print("\n--- AI Tailored Result ---\n" + tailored_latex + "\n" + "-"*25)
            feedback = input("\nAre you satisfied with this version? \nType 'done' to proceed to humanizing, or enter new instructions to refine it again.\n> ")
            current_latex = tailored_latex # Always update to the latest version for the next loop
            if feedback.lower() == 'done':
                break
        else:
            print("Tailoring failed. Please check the error.")
            if input("Try again? (y/n): ").lower() != 'y':
                break

    # --- PHASE 2: HUMANIZING LOOP ---
    print("\n" + "="*50 + "\nPHASE 2: HUMANIZING AND FINALIZING\n" + "="*50)
    final_latex = None
    while True:
        print("\nStarting the chunk-based humanization process...")
        
        extracted_chunks = extract_text_chunks(current_latex)
        if not extracted_chunks:
            if input("Could not extract chunks. Retry? (y/n): ").lower() != 'y': break
            else: continue

        humanized_chunks = []
        all_chunks_humanized = True
        for chunk in extracted_chunks:
            humanized_text = humanize_text(chunk.section_content)
            if humanized_text:
                humanized_chunks.append(TextChunk(section_title=chunk.section_title, section_content=humanized_text))
            else:
                print(f"❌ Failed to humanize section: '{chunk.section_title}'")
                all_chunks_humanized = False
                break
        
        if not all_chunks_humanized:
            if input("Humanization failed on a chunk. Retry the whole process? (y/n): ").lower() != 'y': break
            else: continue
            
        reintegrated_latex = reintegrate_chunks_with_gemini(current_latex, humanized_chunks)
        if not reintegrated_latex:
            if input("Could not re-integrate text. Retry? (y/n): ").lower() != 'y': break
            else: continue
            
        print("\n--- Final Humanized LaTeX Result ---\n" + reintegrated_latex + "\n" + "-" * 35)

        feedback = input("\nAre you satisfied with the humanized version? \nType 'save' to finish, or 'retry' to run the humanize process again.\n> ")
        if feedback.lower() == 'save':
            final_latex = reintegrated_latex
            break
        elif feedback.lower() != 'retry':
            print("Invalid input. Please type 'save' or 'retry'.")
    
    # --- PHASE 3: SAVING THE FILE ---
    if final_latex:
        output_filename = input("\nEnter a filename to save the final .tex file (e.g., 'JohnDoe_Backend.tex'):\n> ")
        if not output_filename.endswith('.tex'):
            output_filename += '.tex'
            
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(final_latex)
        
        print(f"\n✅✅✅ Success! Final resume saved as '{output_filename}' ✅✅✅")
    else:
        print("\nProcess aborted. No file was saved.")