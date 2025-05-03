from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from openai import OpenAI
from openai import AzureOpenAI

from fastapi_mcp import FastApiMCP


from dotenv import load_dotenv
import json
from setup import setup_logging
from resumeparser import app
from fastapi import FastAPI, Depends, Security
from fastapi.security import APIKeyHeader

# Access environment variables
# Load environment variables from .env file

# Set up logging
setup_logging()

apikey= "<<APIkey>>"
api_key_header = APIKeyHeader(name="X-API-Key")

## To be done later
async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != apikey:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# Add MCP server to the FastAPI app
mcp = FastApiMCP(app,name="Resume checker",include_operations=["parse_resume"])

# Mount the MCP server to the FastAPI app
mcp.mount()

mcp.setup_server()





if __name__ == "__main__":
    import uvicorn

    #uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(app, host="127.0.0.1", port=8000)