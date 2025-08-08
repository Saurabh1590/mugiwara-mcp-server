import os
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

# --- CONFIGURATION ---
# We will create a .env file for our secrets later.
# For now, let's define them here.
# IMPORTANT: Replace these with your actual details!
MY_PHONE_NUMBER = "916387384905"  # ❗<-- REPLACE WITH YOUR 10-DIGIT NUMBER PREFIXED WITH 91
MY_SECRET_BEARER_TOKEN = "mugiwaracoder-is-the-best-captain" # This is your secret key

# --- SETUP THE APP ---
app = FastAPI()

# --- TOOL DEFINITIONS ---
# This is where we will define the logic for our tools.

def tool_validate(token: str):
    """The entry-ticket tool required by Puch AI."""
    print(f"Received token for validation: {token}")
    if token == MY_SECRET_BEARER_TOKEN:
        print("✅ Validation successful!")
        return {"phone_number": MY_PHONE_NUMBER}
    else:
        print("❌ Validation FAILED.")
        raise HTTPException(status_code=401, detail="Invalid Bearer Token")

def tool_persona_link(user_text: str):
    """Our main tool. For now, it just replies with a placeholder."""
    # We will add the Gemini AI logic here later.
    print(f"Persona-Link tool called with text: {user_text}")
    return {"message": f"Roger that! I received your text: '{user_text}'. The full analysis engine is coming soon!"}

# A dictionary to map tool names to their functions. This makes our code clean.
AVAILABLE_TOOLS = {
    "validate": tool_validate,
    "persona_link": tool_persona_link, # Our main hackathon tool
}

# --- MCP SERVER ENDPOINT ---
# This is the single endpoint Puch AI will communicate with.

class MCPRequest(BaseModel):
    tool_name: str
    params: dict

@app.post("/mcp")
async def mcp_handler(request: MCPRequest):
    """Handles all incoming requests from Puch AI."""
    tool_name = request.tool_name
    params = request.params
    
    print(f"MCP Handler received request for tool: {tool_name} with params: {params}")

    if tool_name in AVAILABLE_TOOLS:
        tool_function = AVAILABLE_TOOLS[tool_name]
        try:
            # Call the correct tool's function with its parameters
            result = tool_function(**params)
            return result
        except Exception as e:
            # Handle errors gracefully
            print(f"Error executing tool {tool_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")

# A simple root endpoint to check if the server is alive.
@app.get("/")
def read_root():
    return {"status": "MugiwaraCoder's MCP Server is ready to set sail!"}