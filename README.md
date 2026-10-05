# CodeMind AI

CodeMind AI is a multi-agent AI coding system that transforms a software requirement into a working Python project through a structured development workflow.

Instead of relying on a single AI agent, CodeMind AI uses specialized agents for planning, research, coding, testing, and code review.

## Workflow

```text
User Requirement
       ↓
Manager Agent
       ↓
Research Agent
       ↓
Coding Agent
       ↓
Testing Agent
       ↓
 ┌───────────────┐
 │ Tests Pass?   │
 └───────┬───────┘
     Yes │ No
         │
         ↓
     Reviewer
         │
         ↓
      Final
```

When testing fails, the workflow can send the project back to the Coding Agent for another repair attempt before the final review.

## Key Features

* Multi-agent software development workflow
* Requirement analysis and project planning
* Technical research before implementation
* AI-based code generation
* Automated project execution and testing
* Failure-aware coding retry workflow
* Final AI code review
* LangGraph-based workflow orchestration
* Groq-powered LLM agents
* Safe Python project execution
* Modular agent architecture

## Agents

### Manager Agent

Analyzes the user's requirement and creates a development plan.

### Research Agent

Recommends technologies, project structure, implementation approach, edge cases, and testing requirements.

### Coding Agent

Generates the project code based on the research plan.

If testing fails, the Coding Agent receives the previous code and test result and attempts to repair the implementation.

### Testing Agent

Executes the generated project using the project execution tool and reports whether the application passes or fails.

### Reviewer Agent

Reviews the generated implementation together with the test result and produces the final quality assessment.

## Technology Stack

* Python
* LangGraph
* Groq API
* LLM-based Agents
* AST-based Python validation
* Streamlit
* Git / GitHub

## Project Structure

```text
CodeMind_AI/
│
├── agents/
│   ├── manager_agent.py
│   ├── research_agent.py
│   ├── coding_agent.py
│   ├── testing_agent.py
│   └── reviewer_agent.py
│
├── tools/
│   ├── code_executor.py
│   └── project_parser.py
│
├── tests/
│
├── app.py
├── graph.py
├── llm_test.py
├── .env
├── README.md
└── venv/
```

## How It Works

A requirement is provided to CodeMind AI.

For example:

```text
Create a Python calculator application.
```

The Manager Agent creates the development plan.

The Research Agent converts that plan into technical recommendations.

The Coding Agent generates the application.

The Testing Agent executes the generated project and validates the result.

If the project fails, the workflow can return to the Coding Agent with the previous implementation and test failure information.

If the project passes, the Reviewer Agent evaluates the final implementation.

## Example Result

For a Python calculator requirement, CodeMind AI generated a calculator supporting:

* Addition
* Subtraction
* Multiplication
* Division
* Power
* Percentage
* Square root
* CLI usage
* Optional GUI

The generated project was successfully executed and received:

```text
TEST RESULT: PASS
RETRY COUNT: 1
REVIEW STATUS: APPROVED
```

## Installation

Clone the repository:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd CodeMind_AI
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
```

## Running CodeMind AI

Run the LangGraph workflow:

```powershell
venv\Scripts\python.exe graph.py
```

Run the Streamlit application:

```powershell
venv\Scripts\python.exe -m streamlit run app.py
```

## Project Goal

The goal of CodeMind AI is to demonstrate how multiple specialized AI agents can collaborate to automate a software development workflow rather than using a single LLM response for code generation.

The architecture can be extended with additional agents for debugging, documentation, security analysis, deployment, and performance optimization.

## Future Improvements

* Automatic GitHub repository generation
* Automated pull request creation
* More programming language support
* Security review agent
* Documentation agent
* Deployment agent
* Persistent project memory
* Advanced test generation
* Code quality and performance analysis

## Author

Divakar Putta

Built as a practical AI Engineering / Multi-Agent Systems project.
