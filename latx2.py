# File: compile.py
# A simple script to compile an existing .tex file using pdflatex.

import subprocess
import os

def compile_latex(tex_filename):
    """
    Compiles a .tex file to a .pdf using pdflatex.

    Args:
        tex_filename (str): The path to the .tex file.
    """
    # 1. Check if the file exists
    if not os.path.exists(tex_filename):
        print(f"❌ Error: File not found at '{tex_filename}'")
        return

    # Extract the base name for output files
    base_name = os.path.splitext(tex_filename)[0]
    output_pdf_name = base_name + '.pdf'

    print(f"--- Starting compilation for '{tex_filename}' ---")

    # 2. The command to run.
    #    '--interaction=nonstopmode' prevents it from stopping and asking for input on errors.
    command = [
        "pdflatex",
        "--interaction=nonstopmode",
        tex_filename,
    ]

    try:
        # 3. Run the compiler command
        print(f"Running command: {' '.join(command)}")
        process = subprocess.run(
            command,
            check=True,         # Raise an exception if compilation fails (returns non-zero)
            capture_output=True,# Capture the stdout and stderr
            text=True,          # Decode output as text
        )
        print(f"✅ Success! PDF created at '{output_pdf_name}'")

    except FileNotFoundError:
        # This error means pdflatex.exe was not found on the system
        print("❌ CRITICAL ERROR: 'pdflatex' command not found.")
        print("   Please ensure MiKTeX or another LaTeX distribution is installed and its")
        print("   'bin' directory is included in your system's PATH environment variable.")

    except subprocess.CalledProcessError as e:
        # This error means pdflatex ran, but failed due to an error in the .tex file
        print(f"❌ Compilation Failed! pdflatex returned a non-zero exit code: {e.returncode}")
        print("\n--- LaTeX Compiler Log (stdout) ---")
        print(e.stdout)  # The log output from the compiler will be here
        print("---------------------------------")
    
    finally:
        # 4. Clean up the auxiliary files that LaTeX creates
        print("\n--- Cleaning up auxiliary files ---")
        for ext in ['.aux', '.log']:
            aux_file = base_name + ext
            if os.path.exists(aux_file):
                os.remove(aux_file)
                print(f"Removed '{aux_file}'")
        print("---------------------------------")


# --- Main execution block ---
if __name__ == "__main__":
    # Specify the name of the .tex file you want to compile
    file_to_compile = "resume_from_gemini.tex"

    # Run the compilation function
    compile_latex(file_to_compile)