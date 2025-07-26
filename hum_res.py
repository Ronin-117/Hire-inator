# File: process_resume_template_method.py

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Dict
from transformer.app import AcademicTextHumanizer, download_nltk_resources

# --- 1. SETUP AND CONFIGURATION ---
print("🚀 Initializing...")
load_dotenv()

#----HUMANIZER CONFIG____#
download_nltk_resources()
humanizer = AcademicTextHumanizer(
        p_passive=0.3,
        p_synonym_replacement=0.3,
        p_academic_transition=0.4
    )

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY must be set in the .env file.")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# --- 2. PYDANTIC MODELS FOR THE NEW STRUCTURED RESPONSE ---

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

# --- 3. HELPER FUNCTIONS ---

def get_tailored_template_and_chunks(base_latex, job_desc, instructions):
    """
    Uses Gemini to generate both a LaTeX template with placeholders
    and the content for those placeholders.
    """
    print("\n🤖 Sending request to Gemini for template and content generation...")
    
    prompt = f"""
    You are an expert resume editor. Your task is to update the 'BASE LATEX RESUME' based on the provided 'JOB DESCRIPTION' and 'USER INSTRUCTIONS'.Try to make the content in the resume more human like(dont need to use complex language , just simple english).

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
            config={
                "response_mime_type": "application/json",
                "response_schema": TailoredResumeResponse,
            },
        )
        print("✅ Gemini processing complete.")
        return response.parsed
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return None

def humanize_content(chunks: List[ContentChunk]) -> Dict[str, str]:
    """
    A dummy function that simulates humanizing text.
    In this version, it just appends "[humanized]" to the content.
    It returns a dictionary for easy lookup.
    """
    print("\n⚙️ Running dummy humanization process on all chunks...")
    humanized_map = {}
    for chunk in chunks:
        # Replace this line with a real humanizer call if you get one working later
        humanized_text = humanizer.humanize_text(
                            chunk.content,
                            use_passive=True,
                            use_synonyms=True
                        ) + "[HUMANIZED]"
        humanized_map[chunk.title] = humanized_text
        print(f"  - Humanized '{chunk.title}'")
    
    print("✅ Dummy humanization complete.")
    return humanized_map

def populate_template(template: str, content_map: Dict[str, str]) -> str:
    """
    Populates the LaTeX template by directly replacing placeholder keys
    with their corresponding content.
    """
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

# --- 4. SAMPLE DATA ---
# Using your provided sample data
BASE_RESUME_LATEX = r"""
\documentclass[letterpaper,10pt]{article}

\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{xcolor} % <<< FIX 1: Using xcolor for advanced color mixing
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage[default]{sourcesanspro}
\usepackage[T1]{fontenc}
\usepackage{tabularx}
\usepackage{graphicx}
\usepackage{ragged2e} % For the \justifying command

% ------ RESUME STYLING ------
\pagestyle{empty} % No headers or footers

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
    \begin{tabular*}{\textwidth}{@{}p{\textwidth}@{}}
    \small\justifying AI-focused undergraduate studying computer science who is passionate about using data-driven solutions to tackle difficult problems. I have demonstrated success in computer vision and natural language processing while designing and developing machine learning applications. As a Trainee Analyst at TheMathCompany, I aim to use my technical and analytical abilities to produce significant outcomes.
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
        \item \textbf{Languages:} Python, C++, Java, C, SQL
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
        \resumeItem{Developed a full-stack, AI-integrated web application to address a key challenge in the healthcare sector, demonstrating end-to-end project ownership.}
        \resumeItem{Engineered scalable features using Django for the backend and React.js for the interactive frontend.}
    \resumeItemListEnd

    \resumeSubheading
    {InternsChoice}{Bengaluru, KA}
    {AI \& ML Intern}{Mar 2023 -- Apr 2023}
    \resumeItemListStart
        \resumeItem{Applied machine learning techniques to build and deploy practical business solutions, including an image classifier and a customer service chatbot.}
        \resumeItem{Automated key operational processes and improved efficiency by implementing targeted AI solutions.}
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
        \resumeItem{Engineered an AI solution to automate classroom attendance using facial recognition, achieving \textbf{98.9\% accuracy} even in challenging low-light and varied angle conditions.}
    \resumeItemListEnd

    \resumeProjectHeading
        {GrindSensAI: AI-Based Physical Training \& Progress Tracker}
        {https://github.com/Ronin-117/GrindSensAI}
        {Django, React, MediaPipe}
    \resumeItemListStart
        \resumeItem{Built a data-driven fitness application that leverages computer vision to provide real-time form correction and progress tracking for \textbf{over 10 distinct exercises}.}
    \resumeItemListEnd
    
    \resumeProjectHeading
        {Oratis: AI-Powered Interview Preparation Platform}
        {https://github.com/Ronin-117/Mock_Online_InterviewAi}
        {NLP, Computer Vision, API}
    \resumeItemListStart
        \resumeItem{Developed an analytical tool for placement preparation featuring a 3D AI avatar that conducts mock interviews and provides constructive performance feedback.}
    \resumeItemListEnd
    
    \resumeProjectHeading
        {Voxia: Sustainable Project Management Tool using IBM WatsonX}
        {https://github.com/Ronin-117/sustainability-tool}
        {IBM WatsonX, LangChain, API}
    \resumeItemListStart
        \resumeItem{Designed a proof-of-concept for the IBM watsonx challenge to help businesses assess project sustainability, showcasing the ability to leverage enterprise-grade AI for GRC.}
    \resumeItemListEnd
    
    \resumeProjectHeading
        {Custom AI Assistant with RAG}
        {https://github.com/Ronin-117/lang_chain_test}
        {LangChain, NLP, Python}
    \resumeItemListStart
        \resumeItem{Constructed a Retrieval-Augmented Generation (RAG) system to provide accurate, context-aware answers from a specialized knowledge base, a core technique in modern enterprise AI.}
    \resumeItemListEnd
\resumeSubHeadingListEnd

%----------- ACHIEVEMENTS & PUBLICATIONS -----------
\section{Achievements \& Publications}
\resumeSubHeadingListStart
    \resumeItem{\textbf{Secured a Top 10 Finalist position in the IBM watsonx Challenge} for developing "Voxia," an innovative sustainable project management tool at the inaugural IBM Kochi competition.}
    \resumeItem{\textbf{Published Research Paper:} "Oratis: AI Guide to Ace interviews" - Co-authored paper presented at the International Conference on Innovations in Mechanical, Robotics, Computing, and Biomedical Engineering (April 2025).}
    \resumeItem{\textbf{Certifications:} AWS AI Cloud Practitioner (Udemy)[\href{https://drive.google.com/file/d/1hyq1dbVjAA1MLuaTsM54wPWLVKikRFmg/view?usp=sharing}{Certificate}], IBM watsonx.ai Technical Essentials (IBM)[\href{https://drive.google.com/file/d/1jE_tHyAmTK9e3APr32Q-aovg3wDvVlDL/view?usp=sharing}{Certificate}].}
\resumeSubHeadingListEnd

\end{document}
"""
JOB_DESCRIPTION = "We are looking for a Senior Backend Engineer..."

# --- 5. MAIN APPLICATION FLOW ---
if __name__ == "__main__":
    
    user_instructions = input("Enter your instructions to tailor the resume (e.g., 'Emphasize cloud experience').\n> ")

    # Step 1: Get template and chunks
    tailored_response = get_tailored_template_and_chunks(
        BASE_RESUME_LATEX, JOB_DESCRIPTION, user_instructions
    )

    # Add a check to ensure we got a valid response before proceeding
    if not tailored_response:
        print("\nProcess aborted due to an error in the Gemini generation step.")
    else:
        latex_template = tailored_response.latex_template
        content_chunks = tailored_response.content_chunks

        print("\n--- Generated LaTeX Template ---")
        print(latex_template)
        print("\n--- Generated Content Chunks ---")
        for chunk in content_chunks:
            print(f"- {chunk.title}: {chunk.content}")
        
        # Step 2: "Humanize" content
        humanized_content_map = humanize_content(content_chunks)
        
        # Step 3: Populate the template
        final_latex = populate_template(latex_template, humanized_content_map)
        
        print("\n--- FINAL RENDERED LATEX ---")
        print(final_latex)
        print("-" * 30)
        
        # Step 4: Save the final file
        save_feedback = input("Type 'save' to save this file, or anything else to exit.\n> ")
        if save_feedback.lower() == 'save':
            # --- FIX #2 IS HERE ---
            # Check if final_latex is not None before trying to save
            if final_latex:
                output_filename = input("\nEnter a filename (e.g., 'MyTailoredResume.tex'):\n> ")
                if not output_filename.endswith('.tex'):
                    output_filename += '.tex'
                
                with open(output_filename, "w", encoding="utf-8") as f:
                    f.write(final_latex)
                
                print(f"\n✅✅✅ Success! Final resume saved as '{output_filename}' ✅✅✅")
            else:
                print("\n❌ Cannot save. The final LaTeX content is empty due to an earlier error.")
        else:
            print("\nProcess finished. No file was saved.")