import os

OUTPUT_DIR = "outputs"

def save_artifacts(attempt_label, code, review):
    """Save code and review artifacts for inspection."""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        ts_file = os.path.join(OUTPUT_DIR, f"{attempt_label}_code.ts")
        review_file = os.path.join(OUTPUT_DIR, f"{attempt_label}_review.txt")
        
        with open(ts_file, "w", encoding="utf-8") as f:
            f.write(code)
        with open(review_file, "w", encoding="utf-8") as f:
            f.write(review)
            
        print(f"[Artifacts] Saved: {ts_file}")
    except Exception as e:
        print(f"[Artifacts] ERROR: {e}")
