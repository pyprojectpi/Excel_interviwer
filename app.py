import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing in .env file")

genai.configure(api_key=API_KEY)

# FastAPI app setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory session store (for PoC, single user)
chat_history = []

# ------------------------------

# Helper: Generate beginner Excel question (basic & commonly asked)
# ------------------------------
def generate_random_question():
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    prompt = """
You are an expert Excel interviewer. Generate **one basic-to-intermediate Excel interview question** 
suitable for testing a candidate's understanding of Excel fundamentals. Focus on:
- Explaining or defining functions/features (e.g., "What is VLOOKUP?", "What is a pivot table?")
- Differences between similar features (e.g., "Difference between COUNT and COUNTA")
- Advantages/disadvantages of a feature
- Small practical use-case questions (e.g., "How would you highlight overdue tasks?")
Do NOT generate very advanced formulas, macros, or complex scenarios.
Provide only **one question** and nothing else.
"""
    response = model.generate_content(prompt)
    question = response.text.strip() if hasattr(response, "text") else "No question generated."
    return question



# ------------------------------
# Helper: Evaluate candidate's answer
# ------------------------------
def evaluate_answer(question, candidate_answer):
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    prompt = f"""
You are an Excel Interview Evaluator with 10 years of professional experience.
Candidate answered:
\"{candidate_answer}\"
Question:
\"{question}\"

Evaluate the answer in 2-4 sentences.
Include:
- Score (1-10)
- 1-2 strengths
- 1-2 areas to improve
- Final Verdict (Pass/Needs Improvement)
Focus on practical Excel skills and professional usage.
"""
    response = model.generate_content(prompt)
    return response.text.strip() if hasattr(response, "text") else "No feedback generated."

# ------------------------------
# Helper: Generate overall final feedback
# ------------------------------
def generate_final_feedback(chat_history):
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    transcript = "\n".join([f"Q: {c['question']}\nA: {c['answer']}" for c in chat_history])
    prompt = f"""
You are an Excel Interview Evaluator with 10 years of professional experience.
Based on this interview transcript:
{transcript}

Give a short overall evaluation (2-4 sentences).
Include:
- Overall Score (1-10)
- Top 3 strengths
- Top 3 areas to improve
- Final Verdict (Pass/Needs Improvement)
Focus on practical Excel skills and real-world usage.
"""
    response = model.generate_content(prompt)
    return response.text.strip() if hasattr(response, "text") else "No final feedback generated."

# ------------------------------
# Homepage: Start interview
# ------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    global chat_history
    chat_history.clear()
    
    intro_message = "Welcome to the AI-Powered Excel Mock Interviewer! Let's start your interview."
    first_question = generate_random_question()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "chat_history": [{"question": "Intro", "answer": intro_message}],
        "current_question": first_question,
        "feedback": None
    })

# ------------------------------
# Submit candidate answer
# ------------------------------
@app.post("/answer", response_class=HTMLResponse)
async def answer_question(request: Request, candidate_answer: str = Form(...)):
    global chat_history

    # Save candidate answer
    last_question = chat_history[-1]["question"] if chat_history else None
    if last_question != "Intro":
        feedback = evaluate_answer(last_question, candidate_answer)
        chat_history.append({
            "question": last_question,
            "answer": candidate_answer,
            "evaluation": feedback
        })
    else:
        feedback = None

    # Generate next dynamic question
    next_question = generate_random_question()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "chat_history": chat_history,
        "current_question": next_question,
        "feedback": feedback
    })

# ------------------------------
# Run FastAPI via uvicorn
# ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

