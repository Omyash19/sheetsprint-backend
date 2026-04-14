from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai
import os
from dotenv import load_dotenv

# Load your API key from the .env file
load_dotenv()

# Initialize the new GenAI client
client = genai.Client(api_key="AIzaSyDMzy-aJ5PO1cNRtX6JTpeP8Vt60l3lHeo")

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
    try:
        system_prompt = (
            f"You are a Senior Data Analyst. A user is working in a spreadsheet named '{context.sheet_name}'. "
            f"The headers are: {', '.join(context.headers)}. "
            f"The user is at cell {context.cell_address} and wants to: {context.prompt}. "
            "Return ONLY the valid spreadsheet formula starting with '='. "
            "Do not include any text, markdown backticks, or explanations."
        )

        # Using the new SDK syntax
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt
        )
        
        formula = response.text.strip()
        
        if not formula.startswith('='):
            raise ValueError("AI failed to return a valid formula.")

        return {"formula": formula}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)