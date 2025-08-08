from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import math

def custom_cosine_similarity(vec1, vec2):
    """Calculates cosine similarity between two vectors without external libraries."""
    dot_product = sum(p * q for p, q in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(p * p for p in vec1))
    magnitude2 = math.sqrt(sum(q * q for q in vec2))
    if not magnitude1 or not magnitude2:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)

# --- Setup ---
# Set up logging to see messages in Vercel
logging.basicConfig(level=logging.INFO)
app = FastAPI()

# --- Configuration ---
# Make sure these are correct
MY_PHONE_NUMBER = "916387384905" # ❗<-- REPLACE WITH YOUR NUMBER
MY_SECRET_BEARER_TOKEN = "mugiwaracoder-is-the-best-captain"

# --- Tool Logic ---
# These are the actual functions our tools will execute.

def tool_validate(token: str):
    """The entry-ticket tool required by Puch AI."""
    logging.info(f"Validating token...")
    if token == MY_SECRET_BEARER_TOKEN:
        logging.info("✅ Validation successful!")
        return {"phone_number": MY_PHONE_NUMBER}
    else:
        logging.error("❌ Validation FAILED - Invalid Token.")
        raise HTTPException(status_code=401, detail="Invalid Bearer Token")

def tool_mero_ai(user_text: str):
    """Our main tool, Mero AI. For now, it has a placeholder response."""
    logging.info(f"Mero AI tool called with text: '{user_text}'")
    # -----------------------------------------------------------
    # LATER, WE WILL ADD THE GEMINI AI & MATCHING LOGIC HERE
    # -----------------------------------------------------------
    return {
        "message": "💘 Mero Mero Mellow! Your personality is being analyzed... "
                   "Full matching functionality coming soon! #BuildWithPuch"
    }

# A dictionary mapping tool names to their functions
AVAILABLE_TOOLS = {
    "validate": tool_validate,
    "mero-ai": tool_mero_ai,
}

# --- Pydantic Models for JSON-RPC ---
# These models ensure the data from Puch has the correct structure.

class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict
    id: int

# --- Main MCP Server Endpoint ---
# This single endpoint handles ALL communication from Puch.

@app.post("/mcp")
async def mcp_handler(request: JsonRpcRequest):
    method = request.method
    params = request.params
    request_id = request.id
    
    logging.info(f"Received method: {method}")

    # Step 1: Handle the "initialize" handshake
    if method == "initialize":
        logging.info("Handling 'initialize' request.")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "capabilities": {
                    "tools": [
                        {
                            "name": "mero-ai",
                            "description": "Analyzes your personality from text and finds your vibe-twin.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "user_text": {
                                        "type": "string",
                                        "description": "A few sentences about yourself, your hobbies, or what's on your mind."
                                    }
                                },
                                "required": ["user_text"]
                            }
                        }
                    ]
                }
            }
        }

    # Step 2: Handle calls to our actual tools
    elif method in AVAILABLE_TOOLS:
        logging.info(f"Executing tool: {method}")
        tool_function = AVAILABLE_TOOLS[method]
        try:
            result = tool_function(**params)
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as e:
            logging.error(f"Error executing tool {method}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Step 3: Handle unknown methods
    else:
        logging.error(f"Method not found: {method}")
        raise HTTPException(status_code=404, detail=f"Method '{method}' not found.")

@app.get("/")
def read_root():
    return  {"status": "Mero AI Server is ready to captivate! 🚀"}
