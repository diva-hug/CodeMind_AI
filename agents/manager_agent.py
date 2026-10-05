import os 
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client =Groq(api_key=os.getenv("GROQ_API_KEY"))

def manager_agent(requirement):
    prompt=f"""
you are the Manager Agent in CodeMind AI.

your job is  to understand  the software requirement and 
create a clear development plan. 

user requirement {requirement}
Return:
1.Project goal
2.Main task
3.Required technolies
4.Expected Output
""" 

    response =client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role":"system",
                "content":"you are a software engineering manager."
            },
            {
                "role":"user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content

if __name__ =="__main__":

    requirement ="Create a python calculator appplication"

    result =manager_agent(requirement)

    print("\n MANAGER AGENT OUTPUT :-\n")
    print(result)