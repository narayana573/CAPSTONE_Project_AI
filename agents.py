
import fitz
import ollama
import re
import os
import sqlite3
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION ---
MODEL = "qwen2.5-coder:1.5b"
OUTPUT_DIR = "outputs"
DB_PATH = "requirements.db"

# ============================================================================
# DATABASE LAYER (Persistence & Tracking)
# ============================================================================

def init_database():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS requirements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                req_id TEXT UNIQUE NOT NULL,
                feature_name TEXT,
                description TEXT,
                preconditions TEXT,
                user_actions TEXT,
                expected_behavior TEXT,
                validation_handling TEXT,
                full_content TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                generated_code TEXT,
                review_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    print(f"[Database] Initialized at {DB_PATH}")

def store_requirement(req_id, feature_name, description, preconditions, user_actions, expected_behavior, validation_handling, full_content):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO requirements 
                (req_id, feature_name, description, preconditions, user_actions, expected_behavior, validation_handling, full_content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (req_id, feature_name, description, preconditions, user_actions, expected_behavior, validation_handling, full_content))
            conn.commit()
        return True
    except Exception as e:
        print(f"[Database Error] {e}")
        return False

def get_all_requirements():
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute('SELECT * FROM requirements ORDER BY id').fetchall()

def update_requirement_code(req_id, code):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE requirements SET generated_code = ?, status = 'code_generated' WHERE req_id = ?", (code, req_id))
        conn.commit()

def update_requirement_review(req_id, review, status):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE requirements SET review_result = ?, status = ? WHERE req_id = ?", (review, status, req_id))
        conn.commit()

# ============================================================================
# AGENT 2 & 2.1: THE PARALLEL CODERS
# ============================================================================

def agent_2_generate_worker(bundle):
    req_id, req_data, feedback = bundle
    print(f"[Agent 2/2.1] Processing Requirement: {req_id}")
    
    job_sys = (
        "You are an expert Playwright SDET. You must follow the provided requirement fields strictly. "
        "Return ONLY raw TypeScript code. No markdown, no explanations."
    )
    
    # THE STRICT PROMPT
    user_prompt = f"""
    ### STRICT REQUIREMENT TRACEABILITY TASK ###
    Requirement Reference: {req_id}
    Feature Name: {req_data.get('feature_name')}

    You must generate a Playwright TypeScript test covering every element:
    1. DESCRIPTION: {req_data.get('description')}
    2. PRECONDITIONS: {req_data.get('preconditions')}
    3. USER ACTIONS: {req_data.get('user_actions')}
    4. EXPECTED BEHAVIOR: {req_data.get('expected_behavior')}
    5. VALIDATION/ERROR HANDLING: {req_data.get('validation_handling')}

    FEEDBACK TO FIX: {feedback if feedback else 'None.'}

    OUTPUT: Raw TypeScript only. Start with: import {{ test, expect }} from '@playwright/test';
    """
    
    try:
        res = ollama.chat(model=MODEL, messages=[
            {'role': 'system', 'content': job_sys},
            {'role': 'user', 'content': user_prompt}
        ])
        code = res['message']['content'].replace("```typescript", "").replace("```ts", "").replace("```", "").strip()
        update_requirement_code(req_id, code)
        return req_id, code
    except Exception as e:
        print(f"Error generating code for {req_id}: {e}")
        return req_id, None

def agent_2_parallel_generation(req_list, feedback_dict=None):
    feedback_dict = feedback_dict or {}
    tasks = [(r['req_id'], r, feedback_dict.get(r['req_id'], "")) for r in req_list]
    
    results = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        for req_id, code in executor.map(agent_2_generate_worker, tasks):
            if code: results[req_id] = code
    return results

# ============================================================================
# AGENT 3: THE PARALLEL QUALITY REVIEWER
# ============================================================================

def agent_3_review_worker(bundle):
    req_id, code, req_data = bundle
    print(f"[Agent 3] Reviewing: {req_id}")
    
    job_sys = "You are a Senior QA Lead. If the code matches the requirement perfectly, reply 'PASS'. Otherwise, reply 'FIX: [list issues]'."
    
    try:
        res = ollama.chat(model=MODEL, messages=[
            {'role': 'system', 'content': job_sys},
            {'role': 'user', 'content': f"CODE:\n{code}\n\nREQUIREMENT:\n{req_data['user_actions']}"}
        ])
        review = res['message']['content']
        status = 'approved' if review.strip().upper().startswith('PASS') else 'needs_fix'
        update_requirement_review(req_id, review, status)
        return req_id, {'status': status, 'review': review}
    except Exception as e:
        return req_id, {'status': 'error', 'review': str(e)}

def agent_3_parallel_review(generated_codes):
    all_reqs = get_all_requirements()
    # Map for easy lookup during review
    req_map = {r[1]: {'user_actions': r[5]} for r in all_reqs}
    
    tasks = [(rid, code, req_map[rid]) for rid, code in generated_codes.items() if rid in req_map]
    
    results = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        for rid, res in executor.map(agent_3_review_worker, tasks):
            results[rid] = res
    return results

# ============================================================================
# AGENT 1: PDF PARSER
# ============================================================================

def agent_1_read_pdf(file_path):
    print(f"\n[Agent 1] Reading PDF: {file_path}")
    try:
        doc = fitz.open(file_path)
        full_text = "".join([page.get_text("text") for page in doc])
        fr_pattern = r"(FR-[\w]+[-\w]*)"
        fr_matches = list(re.finditer(fr_pattern, full_text))
        
        stored_count = 0
        for i, match in enumerate(fr_matches):
            req_id = match.group(1)
            start_pos = match.start()
            end_pos = fr_matches[i+1].start() if i+1 < len(fr_matches) else len(full_text)
            content = full_text[start_pos:end_pos].strip()
            
            # Simplified logic to populate the fields
            if store_requirement(req_id, req_id, content[:100], "As per PDF", content, "Verified", "Standard", content):
                stored_count += 1
        return stored_count
    except Exception as e:
        print(f"Agent 1 Error: {e}")
        return 0

# ============================================================================
# UTILS
# ============================================================================

def save_artifacts(attempt, code, review, req_id):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, f"{attempt}_{req_id}_log.txt"), "w", encoding="utf-8") as f:
        f.write(f"--- CODE ---\n{code}\n\n--- REVIEW ---\n{review}")

def export_final_suite(final_codes):
    path = os.path.join(OUTPUT_DIR, "final_suite.ts")
    with open(path, "w", encoding="utf-8") as f:
        for rid, code in final_codes.items():
            f.write(f"// Requirement: {rid}\n{code}\n\n")
    return path
