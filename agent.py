# Import necessary classes from the langchain library
from openai import AzureOpenAI

from agents.mcp.server import MCPServerSse
from agents import Agent,Runner

import asyncio

from dotenv import load_dotenv
from pydantic import BaseModel
import os
from resumeparser import ResumeChecklist
from pydantic import BaseModel, Field
from typing import List, Optional
from setup import setup_logging
import os
# Get the current working directory
cwd = os.getcwd()
path= cwd+"/myenv.env"

load_dotenv(dotenv_path=path)

#
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_api_key = os.getenv("AZURE_OPEN_AI_API_KEY")
azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
azure_openai_model = os.getenv("AZURE_OPENAI_DEPLOYMENT")

mcp_server_url = "http://localhost:8000/mcp"
#query the resume parser
# Function to query the resume parser
async def query_resume_parser(input_data: str,mcp_server: MCPServerSse,agent: Agent):
   try:
     
       
       result= await Runner.run(agent, input_data)
       # Ensure result has a final_output attribute or handle it appropriately
       if hasattr(result, 'final_output'):
            return result.final_output
       else:
           raise AttributeError("The result object does not have a 'final_output' attribute.")
   except Exception as e:
        print(f"Error in query_resume_parser: {e}")
        return None
# output of DecisionHire
class DescisionHireOutput(BaseModel):
    decision: str = Field(..., description="Hire/No Hire decision")
    reason: Optional[str] = Field(None, description="Reason for the decision, if applicable")
# Function to create a decision prompt
def createdecisionprompt(role):
    return """
    You are a hiring decision agent. Your task is to evaluate a candidate's resume and make a hiring decision for a specific job role:{role}
    The input will be a structured JSON object containing the following details:
    - Skills: List of technical or professional skills
    - Experience Years: Total number of years of professional experience
    - Education Level: Highest education level attained (e.g. Bachelor's, Master's, PhD)
    - Last Job Role: Most recent or current job title mentioned in the resume
    - Salary Expectation: Salary expectation if explicitly mentioned (annual, USD)
    - Projects Count: Number of distinct projects mentioned or led in the resume
    Based on this information, you need to decide whether to hire the candidate or not.
    Return the decision as "Hire" or "No Hire" along with a reason if applicable.
    return the decision in a structured format such as a JSON object.
    Ensure that the output is clear and concise, and avoid any unnecessary information.
    Example input: {
        "skills": ["Python", "FastAPI"],
        "experience_years": 5,
        "education_level": "Master's",
        "last_job_role": "Software Engineer",
        "salary_expectation": 120000,
        "projects_count": 10
    }
    Example output: {
        "decision": "Hire",
        "reason": "Candidate meets the criteria"
    }
    """


# Function to make a hiring decision
def giveMeDecision(inputdata:ResumeChecklist, role: str ):
    try:
        if inputdata is None:
            raise ValueError("Input data is None")
        # Extract the required fields from the input data
       
        prompt= createdecisionprompt(role)
        messages = [
        {"role": "system", "content": f"{prompt}"},
        {"role": "user", "content": """"Example input: {
        "skills": ["Python", "FastAPI"],
        "experience_years": 5,
        "education_level": "Master's",
        "last_job_role": "Software Engineer",
        "salary_expectation": 120000,
        "projects_count": 10
        }""" },
        {"role": "assistant", "content": "Role is HR manager"+""" { "decision": "Do not Hire","reason": "Candidate does not meet the criteria for the HR manager role."""},
        {"role": "user", "content": """"Example input: {
        "skills": ["Python", "FastAPI"],
        "experience_years": 3,
        "education_level": "Master's",
        "last_job_role": "Software Engineer",
        "salary_expectation": 120000,
        "projects_count": 5
        }""" },
        {"role": "assistant", "content": "Role is senior software engineer."+""" { "decision": "Do not Hire","reason": "Candidate is not good fit for Senior software engineer role as she has only 3 years and not 10 years of experience. Her salary expectation is also high."}"""},
        {"role": "user", "content": """"Example input: {
        "skills": ["Python", "FastAPI",".NET", "C++","Java"],
        "experience_years": 15,
        "education_level": "Master's",
        "last_job_role": "Software Engineer",
        "salary_expectation": 150000,
        "projects_count": 20
        }""" },
        {"role": "assistant", "content": "Role is senior software engineer."+""" { "decision": "Hire","reason": "Candidate is great fit and has sufficient skills and experience."}"""},
        {"role": "user", "content": """"Example input: {
        "skills": ["Multimedia", "Digital marketing","ad sales revenue","print media"],
        "experience_years": 10,
        "education_level": "Master's",
        "last_job_role": "Senior Lead Sales Analyst",
        "salary_expectation": 150000,
        "projects_count": 10
        }""" },
        {"role": "assistant", "content": "Role is Senior Tech leader manager"+""" { "decision": "Hire","reason": "Candidate has sufficient experience in a variety of programming roles and leadership roles."""},
        {"role": "user", "content": """"Example input: {
        "skills": ["Multimedia", "Digital marketing","ad sales revenue","print media"],
        "experience_years": 2,
        "education_level": "Master's",
        "last_job_role": "Junior Sales Analyst",
        "salary_expectation": 150000,
        "projects_count": 2
        }""" },
        {"role": "assistant", "content": "Role is Ad Sales Lead"+""" { "decision": "No Hire","reason": "Candidate does not have sufficient experience to be lead and salary expectation is too high."""},
       
        {"role": "user", "content": f"{inputdata}"}
        ]  
        client = AzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=openai_api_key,
        api_version=azure_openai_api_version
        )
        response = client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=messages,
                response_format=DescisionHireOutput
            )
        resume_data = response.choices[0].message.content 
        #return resume data as DescisionHireOutput object
        if isinstance(resume_data, str):
            resume_data = DescisionHireOutput.parse_raw(resume_data)
        elif isinstance(resume_data, dict):
            resume_data = DescisionHireOutput(**resume_data)
        else:
            raise ValueError("Unexpected response format")

        return resume_data    
    except Exception as e:
        print(f"Error: {e}")
        return None
    
# Main function to run the agent
async def main():
    # Create the MCPServerSse instance
    mcp_server = MCPServerSse(params={"url":mcp_server_url})

    # Connect to the MCP server
    await mcp_server.connect()
    print("Connected to MCP server.")

    tools = await mcp_server.list_tools()
    print(tools)
    #test data
    resumes= []
    roles= []
    test1= "Rajeshwari Mathai has 10 years of experience in .NET,C++,Java,Python and FastAPI. She holds a Master's degree and worked as a Software Engineer. She has been a team leader for past 5 years serving as a guide for 10 team mates. she expects a salary of $120,000 and has led 50 projects."
    resumes.append(test1)
    role1= "Senior Software Engineer"
    roles.append(role1)
    test2= "Sunil Abraham has 10 years of experience in sales and marketing. He holds a Master's degree in multimedia management. He has lead the sales and marketing teams and drove a lot of sales initiatives with great use of multimedia and marketing to capture share of NAM. His last role was Senior Lead Sales Analyst. He expects a salary of $120,000 and has led 20 projects."
    resumes.append(test2)
    role2= "Lead Marketing Analyst"
    roles.append(role2)
    test3= "Rachel Philip has 10 years of experience User Experience and Design. She holds a Phd in Pschychology and UX design. She is proficient in several ux tools like figma. She has developed several UX strategies at her current company with initiatives with Human UX guided design. Her last role was Senior Lead UX Designer. She expects a salary of $150,000 and has led 20 projects."
    resumes.append(test3)
    role3= "Lead UX Designer"
    roles.append(role3)
    test4 = "John Doe has 2 years of experience in Python and FastAPI. He holds a Master's degree and worked as a Software Engineer. He expects a salary of $120,000 and has led 2 projects."
    resumes.append(test4)
    role4= "Software Architect"
    roles.append(role4)
    #get count of resumes
    resumecount= len(resumes) 
    print(f"Number of resumes: {resumecount}")
    print("Processing resumes...")
    agent = Agent(
                name="ResumeAssistant",
                instructions="This agent will parse resumes and determine if resume meets criteria for getting selected or not.",
                mcp_servers=[mcp_server],
                model="gpt-4o",              
                output_type=ResumeChecklist
            )
    for i in range(resumecount):
        resume_text= resumes[i]
        role= roles[i]       
        #Query the resume parser    
        response = await query_resume_parser(resume_text,mcp_server,agent)
        hiringdecision= giveMeDecision(response,role)
        if hiringdecision is None:
            print("No decision made.")
            continue
        print(f"Decision: {hiringdecision.decision}")
        if hiringdecision.reason:
            print(f"Reason: {hiringdecision.reason}")
        else:
            print("No reason provided for the decision.")
     # Connect to the MCP server
    await mcp_server.cleanup()
    print("Cleaned up MCP server connection.")

    


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())