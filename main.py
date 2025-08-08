import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import math
import google.generativeai as genai
import sqlite3

def setup_database():
    """Creates the database and the user_profiles table if they don't exist."""
    conn = sqlite3.connect('mero_ai.db')
    cursor = conn.cursor()
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personality_vector TEXT NOT NULL,
            interests TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

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
setup_database()

# --- Configuration ---
# Make sure these are correct
MY_PHONE_NUMBER = "916387384905" # ❗<-- REPLACE WITH YOUR NUMBER
MY_SECRET_BEARER_TOKEN = "mugiwaracoder-is-the-best-captain"

# This configures the AI with the key from your .env file or Vercel environment variables
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def analyze_text_with_gemini(user_text: str):
    """Calls the Gemini API to analyze personality."""
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        # This is our "secret sauce" prompt
        prompt = f"""
Analyze the provided text to create a psychological profile based on the Five-Factor Model.
Your output must be a valid JSON object with no other text or markdown.
The JSON object should have two keys: "personality_vector" and "interests".

1.  "personality_vector": A list of 5 floating-point numbers between 0.0 and 1.0, representing the user's percentile score for each of the Big Five traits in this exact order: [Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism].
    - Openness: Intellectual curiosity, creativity, preference for novelty.
    - Conscientiousness: Self-discipline, organization, goal-directed behavior.
    - Extraversion: Sociability, assertiveness, gaining energy from social interaction.
    - Agreeableness: Compassion, cooperation, prioritizing social harmony.
    - Neuroticism: Tendency to experience negative emotions like anxiety and stress.
2.  "interests": A list of 5 strings representing the user's most likely interests or hobbies based on the text.

User Text: "{user_text}"
"""

        response = model.generate_content(prompt)
        # Clean up the response to make sure it's valid JSON
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        
        return json.loads(cleaned_response)
    
    except Exception as e:
        logging.error(f"Gemini API Error: {e}")
        return None

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
    """Analyzes text, saves the profile, finds a match, and responds."""
    logging.info(f"Mero AI tool called with text: '{user_text}'")
    
    profile = analyze_text_with_gemini(user_text)
    
    if not profile:
        return {"message": "Sorry, I couldn't analyze the text. Please try again with a bit more detail!"}

    # --- Save the new profile to the database ---
    conn = sqlite3.connect('mero_ai.db')
    cursor = conn.cursor()
    # Convert lists to JSON strings for storage
    personality_str = json.dumps(profile['personality_vector'])
    interests_str = json.dumps(profile['interests'])
    cursor.execute("INSERT INTO user_profiles (personality_vector, interests) VALUES (?, ?)", 
                   (personality_str, interests_str))
    new_user_id = cursor.lastrowid
    conn.commit()

    # --- Find the best match ---
    cursor.execute("SELECT id, personality_vector FROM user_profiles WHERE id != ?", (new_user_id,))
    all_other_profiles = cursor.fetchall()
    conn.close()

    best_match_id = None
    highest_similarity = -1

    if all_other_profiles:
        for other_id, other_p_str in all_other_profiles:
            other_p_vector = json.loads(other_p_str)
            similarity = custom_cosine_similarity(profile['personality_vector'], other_p_vector)
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match_id = other_id
    
    # --- Craft the final, ethical response ---
    interests_output = ", ".join(profile['interests'])
    
    # The ethical framing from the paper!
    response_message = (
        f"💘 **Based on our conversation, here's what I'm sensing:**\n\n"
        f"It seems you enjoy talking about topics like **{interests_output}**. "
        f"The way you express yourself suggests a personality that is thoughtful and unique.\n\n"
    )

    if best_match_id:
        similarity_percent = round(highest_similarity * 100)
        response_message += (
            f"**Connection Found!** 🚀\nI've found another user (ID #{best_match_id}) with a **{similarity_percent}%** similar personality profile. "
            f"You might find you have a lot in common!\n\n"
        )
    else:
        response_message += "You're one of the first to use Mero AI! As more people join, I'll be able to find great matches for you.\n\n"

    response_message += "Share Mero AI with friends! #BuildWithPuch"

    return {"message": response_message}

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
