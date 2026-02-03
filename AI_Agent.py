from typing import TypedDict, List

# Try to import StateGraph from langgraph, but provide a small fallback so this
# module remains importable even if the dependency isn't installed.
try:
    from langgraph.graph import StateGraph, END  # type: ignore
except Exception:
    END = object()

    class StateGraph:
        def __init__(self, state_type):
            self.state_type = state_type
            self.nodes = {}
            self.entry = None
            self.edges = {}
            self.conditional_edges = {}

        def add_node(self, name, fn):
            self.nodes[name] = fn

        def set_entry_point(self, name):
            self.entry = name

        def add_edge(self, src, dst):
            self.edges.setdefault(src, []).append(dst)

        def add_conditional_edges(self, node, decide_fn, mapping):
            self.conditional_edges[node] = (decide_fn, mapping)

        def compile(self):
            # For now, return self as a compiled representation
            return self


class AgentState(TypedDict):
    pdf_content: str
    requirements: List[dict]
    generated_code: str
    audit_report: str
    retry_count: int
    is_satisfied: bool


# Agent functions should live at module level, not inside the TypedDict.
def agent_a_extractor(state: AgentState):
    # Logic: Send pdf_content to an LLM to extract JSON requirements
    # Simulation:
    print("--- AGENT A: EXTRACTING REQUIREMENTS ---")
    return {"requirements": [{"scenario": "Login", "steps": ["Input user", "Click login"]}]}


def agent_b_developer(state: AgentState):
    # Logic: Take requirements (and audit_report if it exists) and write Playwright code
    attempt = state.get('retry_count', 0) + 1
    print(f"--- AGENT B: GENERATING CODE (Attempt {attempt}) ---")
    return {"generated_code": "import { test } from '@playwright/test'; // simulated code"}


def agent_c_auditor(state: AgentState):
    # Logic: Check code for hallucinations, coverage, and missing scenarios
    print("--- AGENT C: AUDITING CODE ---")

    # Example logic: if code doesn't meet coverage, mark satisfied as False
    is_satisfied = False
    report = "Missing edge case: User enters wrong password."

    return {
        "audit_report": report,
        "is_satisfied": is_satisfied,
        "retry_count": state.get('retry_count', 0) + 1
    }


def decide_to_continue(state: AgentState):
    # Check if Auditor is happy or if we hit the capstone limit of 5
    if state.get("is_satisfied") or state.get("retry_count", 0) >= 5:
        return "end"
    else:
        return "rewrite"


# Build the Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("requirement_analyst", agent_a_extractor)
workflow.add_node("playwright_developer", agent_b_developer)
workflow.add_node("quality_auditor", agent_c_auditor)

# Set Entry Point
workflow.set_entry_point("requirement_analyst")

# Connect Nodes
workflow.add_edge("requirement_analyst", "playwright_developer")
workflow.add_edge("playwright_developer", "quality_auditor")

# Add the Conditional Loop (The "Brain")
workflow.add_conditional_edges(
    "quality_auditor",
    decide_to_continue,
    {
        "rewrite": "playwright_developer",
        "end": END
    }
)

app = workflow.compile()

if __name__ == "__main__":
    print("Workflow compiled successfully.")
