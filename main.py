import os
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

# --- CONFIGURATION (No changes here) ---
MY_PHONE_NUMBER = "916387384905"  # ❗<-- Make sure this is your number
MY_SECRET_BEARER_TOKEN = "mugiwaracoder-is-the-best-captain"

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

# class MCPRequest(BaseModel):
#     tool_name: str
#     params: dict

@app.post("/mcp")
async def mcp_handler(request: Request): # <--- CHANGE: Use the generic 'Request'
    """
    This is our debug handler. It will catch the request and show us its true structure.
    """
    # First, get the raw JSON body from the request
    body = await request.json()
    
    # THIS IS THE MOST IMPORTANT LINE. IT PRINTS THE BODY TO OUR LOGS.
    print(f"RAW REQUEST BODY RECEIVED: {body}")
    
    # For now, just return a simple message so Puch doesn't see an error.
    return {"status": "Message received and logged for debugging."}


@app.get("/")
def read_root():
    return {"status": "MugiwaraCoder's MCP Server is ready to set sail! (Debug Mode)"}
