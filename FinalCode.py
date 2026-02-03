import fitz   # For reading the PDF file
import ollama # To talk to the local AI (Deepseek/Llama)
import time
import os
from datetime import datetime

OUTPUT_DIR = "outputs"

# --- CONFIGURATION ---
MODEL = "deepseek-r1:1.5b"  # The AI model you are using
MAX_RETRIES = 5             # Maximum times Agent 3 can ask Agent 2 to fix the code
PDF_PATH = r"D:\VS_code\CAPSTONE_Project\Requirement.pdf"

# --- AGENT 1: THE REQUIREMENT EXTRACTOR ---
def agent_1_read_pdf(file_path):
    print("\n[Agent 1] Reading the PDF file...")
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        print(f"[Agent 1] Successfully pulled out {len(text)} characters of text.")
        return text
    except Exception as e:
        print(f"[Agent 1] ERROR: Could not read file. {e}")
        return None

# --- AGENT 2: THE PLAYWRIGHT CODER ---
def agent_2_generate_code(requirements, feedback=""):
    print("\n[Agent 2] Writing Playwright code...")
    
    # If Agent 3 gave feedback, we tell Agent 2 to fix the errors
    prompt = f"Requirements: {requirements[:2000]}"
    if feedback:
        print(f"[Agent 2] Taking feedback into account to fix the code...")
        prompt += f"\n\nPREVIOUS ERRORS TO FIX: {feedback}"

    job = (
        "You are an expert SDET. Write Playwright TypeScript code based on the requirements. "
        "Provide ONLY the code. No explanations."
    )

    response = ollama.chat(model=MODEL, messages=[
        {'role': 'system', 'content': job},
        {'role': 'user', 'content': prompt}
    ])
    return response['message']['content']

# --- AGENT 3: THE QUALITY REVIEWER ---
def agent_3_review_code(generated_code, requirements):
    print("\n[Agent 3] Reviewing the code for flaws...")
    
    job = (
        "You are a Senior QA Lead. Review the generated Playwright code against the requirements. "
        "Check for: 1. Logic errors 2. Missing steps 3. Hallucinations. "
        "If the code is PERFECT, start your response with the word 'PASS'. "
        "If there are issues, list them clearly so they can be fixed."
    )

    response = ollama.chat(model=MODEL, messages=[
        {'role': 'system', 'content': job},
        {'role': 'user', 'content': f"CODE: {generated_code}\n\nREQUIREMENTS: {requirements[:1000]}"}
    ])
    
    review_result = response['message']['content']
    return review_result

def save_artifacts(attempt_label, code, review, output_dir=OUTPUT_DIR):
    """Save code and review artifacts for inspection."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        ts_file = os.path.join(output_dir, f"{attempt_label}_code.ts")
        review_file = os.path.join(output_dir, f"{attempt_label}_review.txt")
        log_file = os.path.join(output_dir, f"{attempt_label}_log.txt")
        with open(ts_file, "w", encoding="utf-8") as f:
            f.write(code)
        with open(review_file, "w", encoding="utf-8") as f:
            f.write(review)
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"--- CODE ---\n{code}\n\n--- REVIEW ---\n{review}")
        print(f"[Artifacts] Saved files: {ts_file}, {review_file}, {log_file}")
    except Exception as e:
        print(f"[Artifacts] ERROR saving artifacts: {e}")

# --- MAIN CAPSTONE ENGINE ---
def run_capstone_project():
    # 1. Agent 1 starts
    pdf_text = agent_1_read_pdf(PDF_PATH)
    if not pdf_text:
        return

    current_code = ""
    feedback = ""
    attempts = 0

    # 2. The Loop (Agent 2 and Agent 3 working together)
    while attempts < MAX_RETRIES:
        attempts += 1
        print(f"\n--- ATTEMPT {attempts} of {MAX_RETRIES} ---")

        # Agent 2 writes/fixes code
        current_code = agent_2_generate_code(pdf_text, feedback)

        # Agent 3 reviews code
        review = agent_3_review_code(current_code, pdf_text)

        if review.strip().startswith("PASS"):
            print("\n[SUCCESS] Agent 3 approved the code!")
            break
        else:
            print(f"[REJECTED] Agent 3 found issues. Sending back to Agent 2.")
            # Print the review logs to the console for immediate debugging
            print("\n[Agent 3 REVIEW LOGS]\n" + "-"*30)
            print(review)
            print("-"*30 + "\n")

            # Print the current generated code (truncated to avoid terminal flooding if large)
            print("[CURRENT GENERATED CODE] (first 1000 chars shown)\n" + "-"*30)
            print(current_code[:1000])
            print("-"*30 + "\n")

            # Save artifacts so user can inspect files
            save_artifacts(f"attempt_{attempts}", current_code, review)
            print(f"[Artifacts] You can find the files in: {os.path.abspath(OUTPUT_DIR)}")

            # Store feedback for the next loop
            feedback = review # Store feedback for the next loop
            
    # 3. Final Output to User
    print("\n" + "="*50)
    print("FINAL RESULT FOR USER")
    print("="*50)
    print(current_code)
    print("="*50)
    print(f"Project finished after {attempts} attempts.")

    # Save final artifacts and let the user know where they are
    save_artifacts("final", current_code, review if 'review' in locals() else "")
    print(f"[OUTPUT] Final artifacts saved to: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    run_capstone_project()
