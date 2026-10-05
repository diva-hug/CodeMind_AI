import os 
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client =Groq(api_key=os.getenv("GROQ_API_KEY"))

def research_agent(development_plan):
    prompt = f"""
you are the  Research Agent in CodeMind AI.

your job  is to analyze the development plan created by 
the Manager Agent.

Development plan:
{development_plan}

Provide technical  recommendations for  the code Agent.

Include:

1.Recommended Technologies
2. Recommended project structure
3. Important libraries
4. Implementation approach
5. Important edge cases
6. Testing requirements

Do not Write the actual application code.
only provide technical recommendations.

"""
    response =client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role":"system",
                "content":"You are a senior software research engineer."
            },
            {
                "role":"user",
                "content":prompt
            }
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    development_plan = """
    Build a Python calculator application.

    The application should support:
    - Addition
    - Subtraction
    - Multiplication
    - Division
    - Power
    - Square root
    - Percentage

    The application should have a GUI
    and automated tests.
    """

    result = research_agent(development_plan)

    print("\nRESEARCH AGENT OUTPUT:\n")
    print(result)

