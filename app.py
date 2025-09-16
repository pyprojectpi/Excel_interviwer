import streamlit as st
import google.generativeai as genai

# ✅ Configure API key from Streamlit Secrets
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ------------------------------
# Helper: Generate random Excel question
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
    return response.text.strip() if hasattr(response, "text") else "No question generated."

# ------------------------------
# Helper: Evaluate candidate answer
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
# Helper: Generate overall feedback
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
# Streamlit UI
# ------------------------------
st.set_page_config(page_title="🧑‍💻 Excel Mock Interviewer", layout="centered")

st.title("🧑‍💻 AI-Powered Excel Mock Interviewer")
st.write("Welcome! Answer Excel questions and get real-time AI feedback.")

# ✅ Initialize session state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "current_question" not in st.session_state:
    st.session_state["current_question"] = generate_random_question()
if "feedback" not in st.session_state:
    st.session_state["feedback"] = None
if "answer_input" not in st.session_state:
    st.session_state["answer_input"] = ""

# Display past Q&A with evaluations
for chat in st.session_state.chat_history:
    st.markdown(f"**Q:** {chat['question']}")
    st.markdown(f"**Your Answer:** {chat['answer']}")
    if "evaluation" in chat:
        st.success(f"**Evaluation:** {chat['evaluation']}")

# Current question
st.markdown("---")
st.markdown(f"### Current Question: {st.session_state['current_question']}")

# Candidate input
candidate_answer = st.text_area("Your Answer:", key="answer_input")

# Submit button
if st.button("Submit Answer"):
    if candidate_answer.strip():
        feedback = evaluate_answer(st.session_state["current_question"], candidate_answer)
        st.session_state["chat_history"].append({
            "question": st.session_state["current_question"],
            "answer": candidate_answer,
            "evaluation": feedback
        })
        st.session_state["feedback"] = feedback
        st.session_state["current_question"] = generate_random_question()
        # ✅ Safe reset
        st.session_state["answer_input"] = ""

# Show final feedback button
if st.button("Finish Interview"):
    if st.session_state["chat_history"]:
        final_report = generate_final_feedback(st.session_state["chat_history"])
        st.subheader("📊 Final Interview Feedback")
        st.info(final_report)
    else:
        st.warning("Answer at least one question before finishing!")

st.markdown("---")
st.caption("Built with Streamlit + Google Gemini 🚀")
