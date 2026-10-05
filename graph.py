
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from agents.manager_agent import manager_agent
from agents.research_agent import research_agent
from agents.coding_agent import coding_agent
from agents.testing_agent import testing_agent
from agents.reviewer_agent import reviewer_agent


# --------------------------------------------------
# CodeMind State
# --------------------------------------------------

class CodeMindState(TypedDict):
    requirement: str
    manager_plan: str
    research_plan: str
    generated_code: str
    test_result: str
    review_result: str
    retry_count: int


# --------------------------------------------------
# Manager Node
# --------------------------------------------------

def manager_node(state: CodeMindState):

    result = manager_agent(
        state["requirement"]
    )

    return {
        "manager_plan": result
    }


# --------------------------------------------------
# Research Node
# --------------------------------------------------

def research_node(state: CodeMindState):

    result = research_agent(
        state["manager_plan"]
    )

    return {
        "research_plan": result
    }


# --------------------------------------------------
# Coding Node
# --------------------------------------------------

def coding_node(state: CodeMindState):

    result = coding_agent(
        research_plan=state["research_plan"],
        previous_code=state["generated_code"],
        test_result=state["test_result"],
    )

    return {
        "generated_code": result
    }



# --------------------------------------------------
# Testing Node
# --------------------------------------------------

def testing_node(state: CodeMindState):

    result = testing_agent(
        state["generated_code"]
    )

    # Increase retry count after every testing cycle
    current_retry_count = state["retry_count"]

    return {
        "test_result": result,
        "retry_count": current_retry_count + 1
    }


# --------------------------------------------------
# Reviewer Node
# --------------------------------------------------

def review_node(state: CodeMindState):

    result = reviewer_agent(
        state["generated_code"],
        state["test_result"]
    )

    return {
        "review_result": result
    }


# --------------------------------------------------
# Test Router
# --------------------------------------------------

def test_router(state: CodeMindState):

    test_result = state["test_result"]
    retry_count = state["retry_count"]

    # Testing passed
    if "TEST RESULT: PASS" in test_result.upper():
        return "reviewer"

    # Testing failed, but retry limit reached
    if retry_count >= 3:
        return "reviewer"

    # Testing failed, retry coding
    return "coding"


# --------------------------------------------------
# Build LangGraph
# --------------------------------------------------

graph = StateGraph(CodeMindState)


graph.add_node("manager", manager_node)
graph.add_node("research", research_node)
graph.add_node("coding", coding_node)
graph.add_node("testing", testing_node)
graph.add_node("reviewer", review_node)


# --------------------------------------------------
# Main Workflow
# --------------------------------------------------

graph.add_edge(START, "manager")

graph.add_edge("manager", "research")

graph.add_edge("research", "coding")

graph.add_edge("coding", "testing")


# --------------------------------------------------
# Conditional Testing Workflow
# --------------------------------------------------

graph.add_conditional_edges(
    "testing",
    test_router,
    {
        "coding": "coding",
        "reviewer": "reviewer",
    },
)


graph.add_edge("reviewer", END)


# --------------------------------------------------
# Compile Graph
# --------------------------------------------------

app = graph.compile()


# --------------------------------------------------
# Run CodeMind
# --------------------------------------------------

if __name__ == "__main__":

    requirement = "Create a Python calculator application."

    result = app.invoke(
        {
            "requirement": requirement,
            "manager_plan": "",
            "research_plan": "",
            "generated_code": "",
            "test_result": "",
            "review_result": "",
            "retry_count": 0,
        }
    )


    print("\n========== MANAGER PLAN ==========\n")
    print(result["manager_plan"])


    print("\n========== RESEARCH PLAN ==========\n")
    print(result["research_plan"])


    print("\n========== GENERATED CODE ==========\n")
    print(result["generated_code"])


    print("\n========== TEST RESULT ==========\n")
    print(result["test_result"])


    print("\n========== RETRY COUNT ==========\n")
    print(result["retry_count"])


    print("\n========== REVIEW RESULT ==========\n")
    print(result["review_result"])
