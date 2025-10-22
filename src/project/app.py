from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from .models.model import OpenAIHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini handler
openai_handler = OpenAIHandler()

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Models
class Question(BaseModel):
    question: str

    @classmethod
    def as_form(cls, question: str = Form(...)):
        return cls(question=question)

class InterviewSession(BaseModel):
    session_id: Optional[str] = None
    total_questions: int = 2

class UserAnswer(BaseModel):
    session_id: str
    question_number: int
    question_text: str
    answer_text: str

# Temporary storage
interview_sessions = {}
interview_answers = {}

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request}
    )

@app.on_event("startup")
async def startup_event():
    try:
        openai_handler.load_and_clean_squad_hf(limit=5000)
        openai_handler.train_with_examples(num_examples=20)
        print("Gemini model loaded and trained successfully")
    except Exception as e:
        print(f"Error initializing Gemini model: {str(e)}")

@app.post("/api/interview/start")
async def start_interview(session: InterviewSession):
    """Inicia una nueva sesión de entrevista"""
    import uuid
    session_id = str(uuid.uuid4())
    
    interview_sessions[session_id] = {
        "total_questions": session.total_questions,
        "current_question": 0,
        "started_at": str(os.times()),
    }
    
    interview_answers[session_id] = []
    
    return JSONResponse({
        "session_id": session_id,
        "message": "Sesión de entrevista iniciada correctamente",
        "total_questions": session.total_questions
    })

@app.get("/api/interview/question/{session_id}")
async def get_next_question(session_id: str):
    if session_id not in interview_sessions:
        return JSONResponse(
            status_code=404,
            content={"error": "Sesión no encontrada"}
        )
    
    session = interview_sessions[session_id]
    current_q = session["current_question"]

    if current_q >= session["total_questions"]:
        return JSONResponse({
            "completed": True,
            "message": "Entrevista completada"
        })
    
    try:
        # Generar pregunta usando Gemini
        prompt = f"""Genera UNA pregunta de entrevista profesional en español.
        Esta es la pregunta número {current_q + 1} de {session['total_questions']}.
        
        La pregunta debe:
        1. Ser relevante para una entrevista de trabajo
        2. Enfocarse en evaluar competencias profesionales, habilidades o experiencia
        3. Ser clara y específica
        4. Estar formulada en español
        
        Responde SOLO con la pregunta, sin ninguna introducción ni explicación adicional."""

        generated_question = await openai_handler.get_answer("", prompt)
        
        print(generated_question)
        return JSONResponse({
            "completed": False,
            "question_number": current_q + 1,
            "total_questions": session["total_questions"],
            "question_text": generated_question.strip()
        })
        
    except Exception as e:
        print(f"Error generating question: {str(e)}")
        default_questions = [
            "¿Cuál consideras que es tu principal fortaleza profesional?",
            "Describe una situación laboral desafiante y cómo la resolviste.",
            "¿Qué te motiva profesionalmente?",
            "¿Cómo manejas situaciones de presión en el trabajo?",
            "¿Cuál ha sido tu mayor logro profesional hasta ahora?"
        ]
        return JSONResponse({
            "completed": False,
            "question_number": current_q + 1,
            "total_questions": session["total_questions"],
            "question_text": default_questions[current_q % len(default_questions)]
        })

@app.post("/api/interview/answer")
async def save_answer(answer: UserAnswer):
    if answer.session_id not in interview_sessions:
        return JSONResponse(
            status_code=404,
            content={"error": "Sesión no encontrada"}
        )

    interview_answers[answer.session_id].append({
        "question_number": answer.question_number,
        "question": answer.question_text,
        "answer": answer.answer_text,
        "timestamp": str(os.times())
    })

    session = interview_sessions[answer.session_id]
    session["current_question"] += 1

    if session["current_question"] >= session["total_questions"]:
        return JSONResponse({
            "success": True,
            "message": "Respuesta guardada correctamente",
            "completed": True,
            "final_message": "Entrevista completada"
        })

    return JSONResponse({
        "success": True,
        "message": "Respuesta guardada correctamente",
        "completed": False
    })

@app.get("/api/interview/results/{session_id}")
async def get_results(session_id: str):
    if session_id not in interview_sessions:
        return JSONResponse(
            status_code=404,
            content={"error": "Sesión no encontrada"}
        )
    
    answers = interview_answers.get(session_id, [])
    
    return JSONResponse({
        "session_id": session_id,
        "total_questions": interview_sessions[session_id]["total_questions"],
        "answers": answers
    })

@app.delete("/api/interview/session/{session_id}")
async def end_interview(session_id: str):
    if session_id in interview_sessions:
        del interview_sessions[session_id]
    if session_id in interview_answers:
        del interview_answers[session_id]
    
    return JSONResponse({
        "success": True,
        "message": "Sesión finalizada correctamente"
    })

