from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from openai import OpenAI
from openai import AzureOpenAI

from fastapi_mcp import FastApiMCP


from dotenv import load_dotenv

from setup import setup_logging
import json

# Access environment variables
# Load environment variables from .env file
# Get the current working directory
cwd = os.getcwd()
path= cwd+"/myenv.env"

load_dotenv(dotenv_path=path)

#
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_api_key = os.getenv("AZURE_OPEN_AI_API_KEY")
azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
azure_openai_model = os.getenv("AZURE_OPENAI_DEPLOYMENT")


class ResumeChecklist(BaseModel):
    skills: List[str] = Field(..., description="Technical or professional skills listed")
    experience_years: int = Field(..., description="Total number of years of professional experience")
    education_level: str = Field(..., description="Highest education level attained (e.g. Bachelor's, Master's, PhD, BS, BE, Btech, MS, MBA)")
    last_job_role: str = Field(..., description="Most recent or current job title mentioned in resume")
    salary_expectation: Optional[int] = Field(None, description="Salary expectation if explicitly mentioned (annual, USD)")
    projects_count: Optional[int] = Field(None, description="Number of distinct projects mentioned or led in resume")

def create_system_prompt():
    return """
    You are a resume parser. Your task is to extract structured information from resume text.
    The input will be a resume text, and you need to extract the following details:
    - Skills: List of technical or professional skills
    - Experience Years: Total number of years of professional experience
    - Education Level: Highest education level attained (e.g. Bachelor's, Master's, PhD)
    - Last Job Role: Most recent or current job title mentioned in the resume
    - Salary Expectation: Salary expectation if explicitly mentioned (annual, USD)
    - Projects Count: Number of distinct projects mentioned or led in the resume
    return the extracted information in a structured format such as a JSON object.
    Ensure that the output is clear and concise, and avoid any unnecessary information.
    If you cannot find any of the required information, return null for that field.
    Example input: "John Doe has 5 years of experience in Python and FastAPI. He holds a Master's degree and worked as a Software Engineer for 5 years. He expects a salary of $120,000 and has led 10 projects."
    Example output: {   
        "skills": ["Python", "FastAPI"],
        "experience_years": 5,
        "education_level": "Master's",
        "last_job_role": "Software Engineer",
        "salary_expectation": 120000,
        "projects_count": 10
    }
    """

def extract_text_tojson(resume_text):
    try:      
        prompt= create_system_prompt()
        client = AzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=openai_api_key,
        api_version=azure_openai_api_version
        )
        response = client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": resume_text}
                ],                
            )
        resume_data = response.choices[0].message.content           
        
        
        return resume_data
    except Exception as e:
        print(f"Error: {e}")
        return None



def extract_features(resumesummary):
    try:
      
        
        resumesummarytojson= extract_text_tojson(resumesummary)
        
        client = AzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=openai_api_key,
        api_version=azure_openai_api_version
        )
        response = client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": "Extract structured details from the resume provided by the user"},
                    {"role": "user", "content": resumesummarytojson}
                ],
                response_format=ResumeChecklist
            )
        resume_data = response.choices[0].message.content           
        
        
        return resume_data
    except Exception as e:
        print(f"Error: {e}")
        return None

class ResumeInput(BaseModel):
    resume_text: str

app = FastAPI()

@app.get("/",operation_id="root")
def read_root():
    return {"message": "Welcome to the Resume Parser Service!"}

@app.post("/parse_resume", response_model=ResumeChecklist,operation_id="parse_resume")
def parse_resume(input_data: str):
    print("In parse_resume")
    """
    Parses the provided resume text and extracts structured information.
    """
    
    print("resume_text:",input_data)

    # Mock implementation for parsing the resume text
    # Replace this with actual parsing logic
    if not input_data.strip():
        raise HTTPException(status_code=400, detail="Resume text cannot be empty")
    
    parsed_data= extract_features(input_data)
    print("Parsed data:",parsed_data)
    if parsed_data is None:
        raise HTTPException(status_code=500, detail="Failed to parse resume")

    return json.loads(parsed_data)




