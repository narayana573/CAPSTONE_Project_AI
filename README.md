
# AI-Driven Playwright Test Automation Factory

### Capstone Project: Multi-Agent System for Requirement-to-Code Generation

## ## Overview

This project implements a sophisticated **Multi-Agent System (MAS)** that automates the creation of Playwright end-to-end tests from PDF requirement documents. It leverages local LLMs (via Ollama) and parallel processing to achieve high-speed, high-accuracy code generation with an integrated "self-healing" review loop.

---

## ## System Architecture

The system is composed of three specialized agents that operate in a sequential and iterative pipeline:

1. **Agent 1 (The Parser):** Reads the raw PDF, identifies functional requirements (FRs), and structures them into a local SQLite database.
2. **Agent 2 & 2.1 (The Coders):** High-speed workers that generate Playwright TypeScript code based on strict requirement traceability.
3. **Agent 3 (The Reviewer):** A Senior QA Lead agent that validates the generated code against the original requirements and provides feedback for fixes.

---

## ## Detailed Component Explanation

### ### 1. Database Layer (`requirements.db`)

Unlike simple scripts, this system uses **SQLite** for persistence.

* **Purpose:** Tracks the state of every requirement (Pending, Code Generated, Approved, Needs Fix).
* **Benefits:** Prevents data loss and allows the system to skip requirements that are already approved, focusing only on failures during retries.

### ### 2. The Agents (`agents.py`)

#### #### Agent 1: PDF Extractor

* **Library:** `PyMuPDF` (fitz).
* **Logic:** Uses Regular Expressions (`FR-[\w]+`) to segment the PDF into individual requirement blocks.
* **Mapping:** It breaks down the text into specific fields: *ID, Feature Name, Description, Preconditions, User Actions, Expected Behavior, and Validation Handling.*

#### #### Agent 2 & 2.1: Parallel Generation

* **Technology:** `ThreadPoolExecutor` with `Ollama`.
* **Logic:** To increase performance, the workload is split between two virtual workers.
* **Strict Prompting:** The agent is forced to follow a "Traceability Task" where it must map every requirement field to a specific block of Playwright code (e.g., Expected Behavior must become an `expect()` assertion).

#### #### Agent 3: Parallel Reviewer

* **Logic:** Evaluates the generated code.
* **Success Condition:** If the code is perfect, it issues a `PASS`.
* **Failure Condition:** If issues are found, it generates a `FIX:` list. This feedback is fed back into Agent 2 for the next attempt, creating a **Self-Correction Loop**.

### ### 3. Orchestration (`main.py`)

This is the "Brain" of the operation.

* **The Loop:** It runs for a maximum of `MAX_RETRIES` (default 3).
* **Smart Filtering:** In each attempt, it queries the database for requirements that *failed* the previous review and sends only those back to Agent 2 for fixing.
* **Artifacts:** Saves logs, reviews, and code for every attempt in the `outputs/` folder.

---

## ## Workflow Execution Flow

1. **Initialization:** `init_database()` creates the schema.
2. **Ingestion:** `agent_1_read_pdf()` populates the DB with requirements.
3. **Iteration:**
* **Agent 2/2.1** generate code in parallel.
* **Agent 3** reviews code in parallel.
* System saves logs for transparency.


4. **Finalization:** `export_final_suite()` collects all **Approved** tests and merges them into a single, production-ready `final_suite.ts`.

---

## ## Performance Optimization Features

| Feature | Technical Implementation | Impact |
| --- | --- | --- |
| **Parallelism** | `concurrent.futures.ThreadPoolExecutor` | 2x faster code generation and review. |
| **Persistence** | SQLite3 with explicit commits | Reliable tracking and ability to resume work. |
| **Clean Code** | Regex Post-processing | Removes LLM "markdown noise" (```) for valid `.ts` files. |
| **Strict Traceability** | Field-specific LLM Prompting | Ensures 100% coverage of user actions and assertions. |

---

## ## How to Run

1. **Prepare Environment:** Ensure `Ollama` is running with `qwen2.5-coder:1.5b`.
2. **Install Dependencies:** `pip install pymupdf ollama`
3. **Configure Path:** Set `PDF_PATH` in `main.py` to your requirement document.
4. **Execute:** `python main.py`

---
