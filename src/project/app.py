from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from .utils import Utils
from .rag import RAG
from google import genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
API_KEY = os.getenv('GEMINI_API_KEY')
CLIENT = genai.Client()

load_dotenv()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app = FastAPI()

# CORS para permitir peticiones desde el frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = RAG(DB_DIR, CLIENT)
rag.load_database()

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ============== MODELOS ==============
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

# ============== ALMACENAMIENTO TEMPORAL ==============
# En producción, usar base de datos real
interview_sessions = {}
interview_answers = {}

# ============== RUTAS ORIGINALES ==============
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request}
    )

# ============================================
# OLD VERSION
# ============================================


# @app.get("/ask", response_class=HTMLResponse)
# async def ask(request: Request):
#     return templates.TemplateResponse(
#         name="ask.html",
#         context={"request": request}
#     )
#
# @app.post("/answer", response_class=HTMLResponse)
# async def answer(request: Request, text=Depends(Question.as_form)):
#     try:
#         if text is None:
#             raise Exception("No question provided")
#
#         top_docs = rag.search(text.question, k=10)
#         question = Utils._inyect_chunks_into_question(text.question, top_docs)
#
#         return templates.TemplateResponse(
#             "answer.html",
#             {
#                 "request": request,
#                 "question": text.question,
#                 "answer": Utils._generate_answer(CLIENT, question),
#                 "error": None
#             }
#         )
#     except Exception as e:
#         question_text = text.question if text else ""
#         return templates.TemplateResponse(
#             "answer.html",
#             {
#                 "request": request,
#                 "question": question_text,
#                 "answer": Utils._generate_answer(CLIENT, question_text, error=True),
#                 "error": str(e)
#             }
#         )

# ============================================
# ============================================



@app.get("/interview", response_class=HTMLResponse)
async def interview_page(request: Request):
    """Página principal del chatbot de entrevista"""
    return templates.TemplateResponse(
        name="index.html",
        context={"request": request}
    )

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

    if current_q > session["total_questions"]:
        return JSONResponse({
            "completed": True,
            "message": "Entrevista completada"
        })
    
    try:
        context_query = "preguntas de entrevista recursos humanos competencias habilidades"
        top_docs = rag.search(context_query, k=5)
        prompt = f"""Basándote en el siguiente contexto de recursos humanos, genera UNA pregunta de entrevista profesional y relevante.

        Contexto:
        {Utils._inyect_chunks_into_question("", top_docs)}

        Esta es la pregunta número {current_q + 1} de {session['total_questions']}.
        Genera una pregunta clara, profesional y específica sobre competencias, experiencia o habilidades.
        Responde SOLO con la pregunta, sin introducción ni explicación."""

        generated_question = Utils._generate_answer(CLIENT, prompt)
        
        return JSONResponse({
            "completed": False,
            "question_number": current_q + 1,
            "total_questions": session["total_questions"],
            "question_text": generated_question.strip()
        })
        
    except Exception as e:
        default_questions = [
            "¿Cuál es tu experiencia previa en el área de recursos humanos?",
            "Describe una situación donde tuviste que resolver un conflicto laboral."
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

    print(f"pregunta actual {session["current_question"]}")


    if session["current_question"] > session["total_questions"]:
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
    """Obtiene los resultados completos de la entrevista"""
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
    """Finaliza y limpia una sesión de entrevista"""
    if session_id in interview_sessions:
        del interview_sessions[session_id]
    if session_id in interview_answers:
        del interview_answers[session_id]
    
    return JSONResponse({
        "success": True,
        "message": "Sesión finalizada correctamente"
    })

