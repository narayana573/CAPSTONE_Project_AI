import fitz  # PyMuPDF
import ollama
import logging
import json

# 1. Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RequirementExtractorAgent:
    def __init__(self, model_name="deepseek-r1:1.5b"):
        self.model_name = model_name
        logger.info(f"Agent A initialized using Ollama model: {self.model_name}")

    def read_pdf(self, pdf_path):
        """Extracts raw text from a PDF file."""
        logger.info(f"Reading PDF file: {pdf_path}")
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page_num, page in enumerate(doc):
                text += page.get_text()
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF.")
            return text
        except Exception as e:
            logger.error(f"Failed to read PDF: {str(e)}")
            return None

    def extract_testable_requirements(self, raw_text):
        """Sends PDF text to Ollama to identify test scenarios."""
        logger.info("Sending text to Ollama for requirement extraction...")
        
        system_prompt = (
            "You are a Quality Engineering Analyst. Your task is to extract testable "
            "requirements from the provided document text. "
            "Output the result ONLY as a structured JSON list of scenarios. "
            "Each scenario must have: 'id', 'feature', 'scenario_description', and 'steps'."
        )

        try:
            response = ollama.chat(model=self.model_name, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"Extract requirements from this text: {raw_text[:4000]}"} 
            ])
            
            output = response['message']['content']
            logger.info("Ollama successfully generated requirements.")
            return output
        
        except Exception as e:
            logger.error(f"Error during LLM inference: {str(e)}")
            return None

# --- Main Execution Loop ---
if __name__ == "__main__":
    # FIX 2: Set the actual path to your file here. 
    # Use r"" if you are on Windows to avoid path errors.
    file_path = r"D:\VS_code\CAPSTONE_Project\Requirement.pdf" 
    
    # Initialize with your preferred model
    agent_a = RequirementExtractorAgent(model_name="deepseek-r1:1.5b")
    
    # Step 1: Read Data (The file_path is passed into the agent here)
    pdf_data = agent_a.read_pdf(file_path)
    
    if pdf_data:
        # Step 2: Process with Ollama
        requirements_json = agent_a.extract_testable_requirements(pdf_data)
        
        # Log the final output
        print("\n--- FINAL EXTRACTED REQUIREMENTS ---")
        print(requirements_json)
