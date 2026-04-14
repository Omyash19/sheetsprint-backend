import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv

# 1. Load the environment (Works for .env locally and Render in the cloud)
load_dotenv()

# 2. Get the key securely from the system environment
api_key = os.getenv("GEMINI_API_KEY")

# 3. Debugging (Check these in Render Logs to verify the vault is working)
if not api_key:
    print("DEBUG: GEMINI_API_KEY is EMPTY!")
else:
    print(f"DEBUG: Key found (starts with: {api_key[:5]}...)")

# 4. Initialize the Client ONE TIME using the secure variable
if api_key:
    client = genai.Client(api_key=api_key)
else:
    # This prevents the app from crashing entirely if the key is missing
    client = None
    print("DEBUG: No API key found in environment! Client not initialized.")

app = FastAPI(title="FormulaFlow AI Engine")

class SheetContext(BaseModel):
    prompt: str
    headers: list
    cell_address: str
    sheet_name: str

@app.get("/")
def home():
    return {"status": "AI Engine is Online"}

@app.post("/generate-formula")
async def generate_formula(context: SheetContext):
    # Safety check in case the client failed to initialize
    if not client:
        raise HTTPException(status_code=500, detail="GenAI client is not initialized. Check your GEMINI_API_KEY in Render.")

    try:
        system_prompt = (
            f"You are a Senior Data Analyst. A user is working in a spreadsheet named '{context.sheet_name}'. "
            f"The headers are: {', '.join(context.headers)}. "
            f"The user is at cell {context.cell_address} and wants to: {context.prompt}. "
            "Return ONLY the valid spreadsheet formula starting with '='. "
            "Do not include any text, markdown backticks, or explanations."
        )

        # Generating the formula using the latest flash model
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=system_prompt
        )
        
        formula = response.text.strip()
        
        # Clean up any potential markdown backticks the AI might add
        if "```" in formula:
            formula = formula.replace("```excel", "").replace("```", "").strip()
            
        if not formula.startswith('='):
            raise ValueError("AI failed to return a valid formula.")

        return {"formula": formula}
    
    except Exception as e:
        print(f"Error during formula generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Crucial for Render: dynamically bind to the port Render assigns, default to 8000 locally
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
