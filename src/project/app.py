import os
import json
import uuid
import logging
from typing import Optional, List, Dict

# FastAPI
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Redis
import redis

# Project modules
from project.rag.question_generator import QuestionGenerator
from project.rag.answer_generator import AnswerGenerator
from project.metrics.feedback_service import FeedbackService
from project.metrics.explanation_service import ExplanationService
from project.rag.gemini_rag_service import GeminiTheoryService

# IMPORTANTE: Importamos tu nuevo evaluador avanzado
# Asegúrate de que el archivo evaluator.py que subiste esté en project/metrics/evaluator.py
from project.metrics.evaluator import evaluate_full

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN ---
TOTAL_QUESTIONS = 2
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv()

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app = FastAPI()

# Configuración de Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info(f"Conectado a Redis en {REDIS_URL}")
except redis.ConnectionError:
    logger.warning("No se pudo conectar a Redis. Usando almacenamiento en memoria (NO apto para múltiples workers).")
    class MockRedis:
        def __init__(self): self.data = {}
        def get(self, key): return self.data.get(key)
        def set(self, key, value): self.data[key] = value
        def delete(self, key): self.data.pop(key, None)
    redis_client = MockRedis()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicialización de servicios
question_generator = QuestionGenerator(dataset_type="squad")
answer_generator = AnswerGenerator()
feedback_service = FeedbackService()
explanation_service = ExplanationService()
theory_service = GeminiTheoryService()

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# --- MODELOS ---
class Question(BaseModel):
    question: str
    @classmethod
    def as_form(cls, question: str = Form(...)):
        return cls(question=question)

class InterviewSession(BaseModel):
    session_id: Optional[str] = None
    total_questions: int = 3
    dataset_type: str = "natural_questions"

class UserAnswer(BaseModel):
    session_id: str
    question_number: int
    question_text: str
    answer_text: str

class HintRequest(BaseModel):
    session_id: str
    question_number: int

# --- HELPERS REDIS ---
def get_session(session_id: str):
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else None

def save_session(session_id: str, data: dict):
    redis_client.set(f"session:{session_id}", json.dumps(data))

def get_answers(session_id: str) -> List[dict]:
    data = redis_client.get(f"answers:{session_id}")
    return json.loads(data) if data else []

def save_answers(session_id: str, data: List[dict]):
    redis_client.set(f"answers:{session_id}", json.dumps(data))

def get_questions_map(session_id: str) -> dict:
    data = redis_client.get(f"qmap:{session_id}")
    return json.loads(data) if data else {}

def save_questions_map(session_id: str, data: dict):
    redis_client.set(f"qmap:{session_id}", json.dumps(data))

# --- BACKGROUND TASK ---
def process_evaluation_task(session_id: str, question_number: int, user_answer: str, correct_answer: str):
    """
    Tarea en segundo plano: Ejecuta evaluate_full (SymPy, SBERT, etc.)
    y actualiza la respuesta en Redis con la clave 'metrics'.
    """
    logger.info(f"[Background] Iniciando evaluación avanzada para {session_id} - P{question_number}")
    try:
        # 1. Cálculo pesado con tu nuevo evaluador
        metrics = evaluate_full(
            correct_answer=correct_answer,
            user_answer=user_answer
        )
        
        # 2. Actualizar Redis
        answers = get_answers(session_id)
        updated = False
        for ans in answers:
            if ans["question_number"] == question_number:
                ans["metrics"] = metrics  # Guardamos como 'metrics' para el frontend
                updated = True
                break
        
        if updated:
            save_answers(session_id, answers)
            logger.info(f"[Background] Métricas guardadas para P{question_number}: {metrics.get('final_score')}")
        else:
            logger.warning(f"[Background] No se encontró respuesta para actualizar P{question_number}")

    except Exception as e:
        logger.error(f"[Background] Error CRÍTICO en evaluación: {e}")

# --- ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})

@app.get("/api/datasets")
async def get_available_datasets():
    return JSONResponse({
        "datasets": [
            {"id": "squad", "name": "SQuAD", "description": "Stanford Question Answering Dataset"},
            {"id": "coachquant", "name": "CoachQuant", "description": "Preguntas de entrevista cuantitativas"}
        ]
    })

@app.post("/api/interview/start")
async def start_interview(session: InterviewSession):
    session_id = str(uuid.uuid4())

    # Configurar dataset
    if session.dataset_type != question_generator.dataset_type:
        try:
            # Ahora usamos session.total_questions
            question_generator.set_dataset(session.dataset_type) 
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    # Inicializar estado en Redis
    session_data = {
        "total_questions": session.total_questions, # Usa el valor del cliente
        "current_question": 0,
        "started_at": str(os.times()),
        "dataset_type": session.dataset_type,
    }
    save_session(session_id, session_data)
    save_answers(session_id, [])
    save_questions_map(session_id, {})

    return JSONResponse({
        "session_id": session_id,
        "message": "Sesión iniciada",
        "total_questions": session.total_questions,
        "dataset_type": session.dataset_type,
    })

@app.get("/api/interview/question/{session_id}")
async def get_next_question(session_id: str):
    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Sesión no encontrada"})

    current_q = session["current_question"]
    if current_q >= session["total_questions"]:
        return JSONResponse({"completed": True, "message": "Entrevista completada"})

    try:
        raw_question, raw_answer = question_generator.generate_single_question_with_answer()
        if not raw_question:
            raw_question, raw_answer = "Error generando pregunta.", ""

        clean_question = raw_question
        clean_answer = answer_generator.clean_answer(raw_answer)

        q_map = get_questions_map(session_id)
        q_map[str(current_q + 1)] = {
            "question_text": clean_question,
            "correct_answer": clean_answer
        }
        save_questions_map(session_id, q_map)

        return JSONResponse({
            "completed": False,
            "question_number": current_q + 1,
            "total_questions": session["total_questions"],
            "question_text": clean_question,
            "correct_answer": clean_answer
        })

    except Exception as e:
        logger.error(f"Error endpoint question: {e}")
        return JSONResponse(status_code=500, content={"error": "Error interno"})

@app.post("/api/interview/answer")
async def save_answer(answer: UserAnswer, background_tasks: BackgroundTasks):
    session = get_session(answer.session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Sesión no encontrada"})

    q_map = get_questions_map(answer.session_id)
    q_data = q_map.get(str(answer.question_number))
    if not q_data:
        return JSONResponse(status_code=400, content={"error": "Datos de pregunta perdidos"})

    new_answer = {
        "question_number": answer.question_number,
        "question": answer.question_text,
        "answer": answer.answer_text,
        "correct_answer": q_data["correct_answer"],
        "timestamp": str(os.times()),
        "feedback": None,
        "explanation": None,
        "metrics": None # Inicializamos en None, el background worker lo llenará
    }

    answers_list = get_answers(answer.session_id)
    answers_list.append(new_answer)
    save_answers(answer.session_id, answers_list)

    session["current_question"] += 1
    save_session(answer.session_id, session)

    # Lanzar tarea pesada
    background_tasks.add_task(
        process_evaluation_task,
        answer.session_id,
        answer.question_number,
        answer.answer_text,
        q_data["correct_answer"]
    )

    completed = session["current_question"] >= session["total_questions"]
    return JSONResponse({
        "success": True,
        "message": "Respuesta recibida.",
        "completed": completed
    })

@app.post("/api/interview/hint")
async def get_hint(payload: HintRequest):
    session_id = payload.session_id
    try:
        q_map = get_questions_map(session_id)
        q_data = q_map.get(str(payload.question_number))

        if not q_data:
            return JSONResponse(status_code=400, content={"error": "Pregunta no encontrada"})

        hint = answer_generator.generate_hint(
            question=q_data["question_text"], 
            correct_answer=q_data["correct_answer"]
        )
        return JSONResponse({"hint": hint})

    except Exception as e:
        logger.error(f"Error en hint: {e}")
        return JSONResponse(status_code=500, content={"error": "Error generando pista"})

@app.post("/api/feedback")
async def generate_feedback(payload: dict):
    # Pasamos las métricas al feedback service para que el LLM sea consciente de la nota
    try:
        feedback = feedback_service.generate_feedback(
            question=payload.get("question"),
            correct_answer=payload.get("correct_answer"),
            user_answer=payload.get("user_answer"),
            evaluation=payload.get("metrics") # El servicio espera un dict de evaluación
        )
        return JSONResponse({"feedback": feedback})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/explanation")
async def generate_explanation(payload: dict):
    session_id = payload.get("session_id")
    question_number = payload.get("question_number")
    
    answers = get_answers(session_id)
    target_ans = next((a for a in answers if a["question_number"] == question_number), None)
    
    if target_ans and target_ans.get("explanation"):
        return JSONResponse({"explanation": target_ans["explanation"]})

    try:
        explanation = explanation_service.generate_explanation(
            payload.get("question"),
            payload.get("correct_answer")
        )
        
        if target_ans:
            target_ans["explanation"] = explanation
            save_answers(session_id, answers)
            
        return JSONResponse({"explanation": explanation})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/theory")
async def get_theory(payload: dict):
    explanation = theory_service.get_theory_explanation(payload.get("question"))
    return JSONResponse({"theory": explanation})

@app.get("/results/{session_id}", response_class=HTMLResponse)
async def show_results_page(request: Request, session_id: str):
    session = get_session(session_id)
    if not session:
        return HTMLResponse("<h1>Sesión no encontrada</h1>", status_code=404)

    answers = get_answers(session_id)
    
    # Procesamiento final antes de enviar al frontend
    for ans in answers:
        # Si por alguna razón el background task no terminó o falló (Redis tiene metrics: None)
        # calculamos las métricas en este momento para que no se rompa la UI
        if not ans.get("metrics"):
            logger.info(f"Calculando métricas on-the-fly para {session_id} P{ans['question_number']}")
            try:
                ans["metrics"] = evaluate_full(ans["correct_answer"], ans["answer"])
            except Exception as e:
                logger.error(f"Error fallback metrics: {e}")
                ans["metrics"] = {} # Evitar crash en frontend

    # Ya no calculamos BLEU/ROUGE global aquí. 
    # El frontend (results.js) se encarga de mostrar los promedios de 'metrics'.

    data = {
        "session_id": session_id,
        "total_questions": len(answers),
        "dataset_type": session.get("dataset_type", "squad"),
        "answers": answers
        # Eliminadas las claves antiguas: bleu, rouge, bertscore
    }
    
    return templates.TemplateResponse("results.html", {"request": request, "data": data})

@app.delete("/api/interview/session/{session_id}")
async def end_interview(session_id: str):
    redis_client.delete(f"session:{session_id}")
    redis_client.delete(f"answers:{session_id}")
    redis_client.delete(f"qmap:{session_id}")
    return JSONResponse({"success": True, "message": "Sesión finalizada"})