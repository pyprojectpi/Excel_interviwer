import os
import google.generativeai as genai
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing in .env file")

genai.configure(api_key=API_KEY)

# FastAPI app
app = FastAPI()

# Mount static & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory session store
chat_history = []

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "chat_history": chat_history,
        "feedback": None
    })

@app.post("/ask", response_class=HTMLResponse)
async def ask_question(request: Request, question: str = Form(...)):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")

        # Prompt: 10-year Excel expert mindset
        prompt = f"""You are an Excel Interviewer with 10 years of professional experience.
Candidate Question: {question}
Answer in **2-4 correct sentences like a senior Excel expert** only.
Keep it clear, precise, and professional, focusing on real-world usage and best practices.
Do NOT write long tutorials, step-by-step guides, or essays."""

        response = model.generate_content(prompt)
        answer = response.text.strip() if hasattr(response, "text") else "No response from model."
    except Exception as e:
        answer = f"Error: {str(e)}"

    # Save Q&A to chat history
    chat_history.append({"question": question, "answer": answer})

    return templates.TemplateResponse("index.html", {
        "request": request,
        "chat_history": chat_history,
        "feedback": None
    })

@app.post("/end", response_class=HTMLResponse)
async def end_interview(request: Request):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        transcript = "\n".join([f"Q: {c['question']}\nA: {c['answer']}" for c in chat_history])

        # Feedback prompt: Always aim for 9-10 if knowledge is solid
        feedback_prompt = f"""You are an Excel Interview Evaluator with 10 years of professional experience.
Based on this interview transcript:
{transcript}

Give a **short evaluation in 2-4 sentences** only.
Include:
   - Overall Score (aim for 9-10 if the candidate demonstrates solid Excel knowledge)
   - 1-2 strengths
   - 1-2 areas to improve
   - Final Verdict (Pass/Needs Improvement)
Focus on practical Excel skills, real-world usage, and professional competency.
Make the feedback professional, concise, and encouraging.
Do NOT write long paragraphs or detailed explanations."""

        response = model.generate_content(feedback_prompt)
        feedback = response.text.strip() if hasattr(response, "text") else "No feedback generated."
    except Exception as e:
        feedback = f"Error: {str(e)}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "chat_history": chat_history,
        "feedback": feedback
    })
