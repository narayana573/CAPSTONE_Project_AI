import fitz  # Library to read PDF files
import ollama # Library to talk to your local AI
import json

# --- STEP 1: READ THE PDF FILE ---
def get_text_from_pdf(file_path):
    print(f"1. Opening file: {file_path}")
    try:
        # Open the PDF document
        doc = fitz.open(file_path)
        content = ""
        
        # Go through every page and pull out the text
        for page in doc:
            content += page.get_text()
            
        print("   - PDF read successfully!")
        return content
    except Exception as e:
        print(f"   - Error reading file: {e}")
        return None

# --- STEP 2: ASK THE AI TO EXTRACT TESTS ---
def get_ai_requirements(text):
    print("2. Sending text to AI (Ollama)...")
    
    # We tell the AI exactly what its job is (System Prompt)
    job_description = "You are a software tester. Read this text and list the test cases as JSON only."
    
    try:
        # We send the text to the model
        response = ollama.chat(
            model="deepseek-r1:1.5b", 
            messages=[
                {'role': 'system', 'content': job_description},
                {'role': 'user', 'content': text[:3000]} # We only send the first 3000 letters to keep it fast
            ]
        )
        print("   - AI has finished processing!")
        return response['message']['content']
    except Exception as e:
        print(f"   - AI Error: {e}")
        return None

# --- STEP 3: RUN EVERYTHING ---
if __name__ == "__main__":
    # Put your file location here
    my_file = r"D:\VS_code\CAPSTONE_Project\Requirement.pdf"
    
    # Run Part 1
    raw_text = get_text_from_pdf(my_file)
    
    if raw_text:
        # Run Part 2
        final_json = get_ai_requirements(raw_text)
        
        # Show the result on the screen
        print("\n--- YOUR TEST REQUIREMENTS ---")
        print(final_json)