
from agents import (
    agent_1_read_pdf, 
    agent_2_parallel_generation,
    agent_3_parallel_review,
    init_database,
    get_all_requirements,
    save_artifacts,
    export_final_suite,
    DB_PATH
)
import sqlite3
import os

PDF_PATH = r"D:\VS_code\CAPSTONE_Project_AI\Requirement.pdf"
MAX_RETRIES = 3

def run_capstone():
    print("\n" + "="*60)
    print("CAPSTONE: MULTI-AGENT PLAYWRIGHT GENERATOR")
    print("="*60)

    init_database()
    
    count = agent_1_read_pdf(PDF_PATH)
    if count == 0: 
        print("No requirements found. Exiting.")
        return

    attempts = 0
    failing_req_ids = []
    feedback_map = {}

    while attempts < MAX_RETRIES:
        attempts += 1
        print(f"\n--- ATTEMPT {attempts} of {MAX_RETRIES} ---")

        raw_db = get_all_requirements()
        to_process = []
        
        for r in raw_db:
            # Row mapping: id=0, req_id=1, feat=2, desc=3, pre=4, actions=5, exp=6, val=7
            if attempts == 1 or r[1] in failing_req_ids:
                to_process.append({
                    'req_id': r[1], 'feature_name': r[2], 'description': r[3],
                    'preconditions': r[4], 'user_actions': r[5], 
                    'expected_behavior': r[6], 'validation_handling': r[7]
                })

        if not to_process:
            print("[Success] All tests passed review!")
            break

        # Parallel Work
        generated_codes = agent_2_parallel_generation(to_process, feedback_map)
        review_results = agent_3_parallel_review(generated_codes)

        failing_req_ids = []
        feedback_map = {}
        for rid, res in review_results.items():
            if rid in generated_codes:
                save_artifacts(f"attempt_{attempts}", generated_codes[rid], res['review'], rid)
                if res['status'] != 'approved':
                    failing_req_ids.append(rid)
                    feedback_map[rid] = res['review']

    # Final Export
    with sqlite3.connect(DB_PATH) as conn:
        final_rows = conn.execute("SELECT req_id, generated_code FROM requirements WHERE status='approved'").fetchall()
        final_codes = {row[0]: row[1] for row in final_rows}

    if final_codes:
        path = export_final_suite(final_codes)
        print(f"\n[Finished] Total Approved: {len(final_codes)}")
        print(f"[File] Final Suite saved at: {os.path.abspath(path)}")
    else:
        print("\n[Warning] No tests were approved. Check logs in 'outputs' folder.")

if __name__ == "__main__":
    run_capstone()
