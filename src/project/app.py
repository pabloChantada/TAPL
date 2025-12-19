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
from project.metrics.evaluator import evaluate_full

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN ---
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
    """Modelo para representar una pregunta."""
    question: str
    @classmethod
    def as_form(cls, question: str = Form(...)):
        return cls(question=question)

class InterviewSession(BaseModel):
    """Modelo para la configuración de una sesión de entrevista."""
    session_id: Optional[str] = None
    total_questions: int = 3
    dataset_type: str = "natural_questions"
    difficulty_level: str = "Facil" # Facil | Medio | Dificil

class UserAnswer(BaseModel):
    """Modelo para recibir la respuesta del usuario."""
    session_id: str
    question_number: int
    question_text: str
    answer_text: str

class HintRequest(BaseModel):
    """Modelo para solicitar una pista."""
    session_id: str
    question_number: int

# --- HELPERS REDIS ---
def get_session(session_id: str):
    """Recupera los datos de la sesión desde Redis."""
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else None

def save_session(session_id: str, data: dict):
    """Guarda los datos de la sesión en Redis."""
    redis_client.set(f"session:{session_id}", json.dumps(data))

def get_answers(session_id: str) -> List[dict]:
    """Recupera la lista de respuestas de una sesión."""
    data = redis_client.get(f"answers:{session_id}")
    return json.loads(data) if data else []

def save_answers(session_id: str, data: List[dict]):
    """Guarda la lista de respuestas en Redis."""
    redis_client.set(f"answers:{session_id}", json.dumps(data))

def get_questions_map(session_id: str) -> dict:
    """Recupera el mapa de preguntas de una sesión."""
    data = redis_client.get(f"qmap:{session_id}")
    return json.loads(data) if data else {}

def save_questions_map(session_id: str, data: dict):
    """Guarda el mapa de preguntas en Redis."""
    redis_client.set(f"qmap:{session_id}", json.dumps(data))

# --- BACKGROUND TASK ---
def process_evaluation_task(session_id: str, question_number: int, user_answer: str, correct_answer: str):
    """
    Tarea en segundo plano: Ejecuta la evaluación completa y actualiza la respuesta en Redis.
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
    """Renderiza la página de inicio."""
    return templates.TemplateResponse(name="index.html", context={"request": request})

@app.get("/api/datasets")
async def get_available_datasets():
    """Devuelve la lista de datasets disponibles."""
    return JSONResponse({
        "datasets": [
            {"id": "squad", "name": "SQuAD", "description": "Stanford Question Answering Dataset"},
            {"id": "coachquant", "name": "CoachQuant", "description": "Preguntas de entrevista cuantitativas"}
        ]
    })

@app.post("/api/interview/start")
async def start_interview(session: InterviewSession):
    """Inicia una nueva sesión de entrevista."""
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
        "total_questions": session.total_questions,
        "current_question": 0,
        "started_at": str(os.times()),
        "dataset_type": session.dataset_type,
        "current_difficulty": session.difficulty_level.title(),
        "streak_correctas": 0
    }
    save_session(session_id, session_data)
    save_answers(session_id, [])
    save_questions_map(session_id, {})

    return JSONResponse({
        "session_id": session_id,
        "message": "Sesión iniciada",
        "total_questions": session.total_questions,
        "dataset_type": session.dataset_type,
        "difficulty_level": session.difficulty_level.title(),
    })

@app.get("/api/interview/question/{session_id}")
async def get_next_question(session_id: str):
    """Obtiene la siguiente pregunta para la sesión actual."""
    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Sesión no encontrada"})

    current_q = session["current_question"]
    if current_q >= session["total_questions"]:
        return JSONResponse({"completed": True, "message": "Entrevista completada"})

    try:
        target_level = session.get("current_difficulty", "Facil")
        raw_question, raw_answer, detected_level = question_generator.generate_single_question_with_answer(
            target_difficulty=target_level
        )
        if not raw_question:
            raw_question, raw_answer = "Error generando pregunta.", ""
            detected_level = target_level

        clean_question = raw_question
        clean_answer = answer_generator.clean_answer(raw_answer)

        q_map = get_questions_map(session_id)
        q_map[str(current_q + 1)] = {
            "question_text": clean_question,
            "correct_answer": clean_answer,
            "difficulty": detected_level
        }
        save_questions_map(session_id, q_map)

        return JSONResponse({
            "completed": False,
            "question_number": current_q + 1,
            "total_questions": session["total_questions"],
            "question_text": clean_question,
            "correct_answer": clean_answer,
            "difficulty": detected_level
        })

    except Exception as e:
        logger.error(f"Error endpoint question: {e}")
        return JSONResponse(status_code=500, content={"error": "Error interno"})

@app.post("/api/interview/answer")
async def save_answer(answer: UserAnswer, background_tasks: BackgroundTasks):
    """Guarda la respuesta del usuario y evalúa el desempeño."""
    session = get_session(answer.session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Sesión no encontrada"})

    q_map = get_questions_map(answer.session_id)
    q_data = q_map.get(str(answer.question_number))
    if not q_data:
        return JSONResponse(status_code=400, content={"error": "Datos de pregunta perdidos"})

    # Evaluamos inline para tener métricas inmediatas
    metrics_now = evaluate_full(
        correct_answer=q_data["correct_answer"],
        user_answer=answer.answer_text
    )

    new_answer = {
        "question_number": answer.question_number,
        "question": answer.question_text,
        "answer": answer.answer_text,
        "correct_answer": q_data["correct_answer"],
        "difficulty": q_data.get("difficulty", session.get("current_difficulty", "Facil")),
        "timestamp": str(os.times()),
        "feedback": None,
        "explanation": None,
        "metrics": metrics_now
    }

    answers_list = get_answers(answer.session_id)
    answers_list.append(new_answer)
    save_answers(answer.session_id, answers_list)

    # --- LÓGICA DE PROGRESIÓN DE DIFICULTAD ---
    final_score = metrics_now.get("final_score", 0)
    curr_level = session.get("current_difficulty", "Facil")
    streak = session.get("streak_correctas", 0)
    
    # Solo ajustamos dificultad si NO es la última pregunta
    if session["current_question"] < session["total_questions"]:
        
        # Promoción: Requiere nota alta (>= 0.85)
        if final_score >= 0.85:
            streak += 1
        else:
            streak = 0 # Reiniciar racha si falla o es mediocre

        # Subir nivel tras 2 aciertos seguidos
        if streak >= 2:
            if curr_level == "Facil":
                curr_level = "Medio"
            elif curr_level == "Medio":
                curr_level = "Dificil"
            streak = 0  # reset tras subir

        # Bajada inmediata con fallo claro (< 0.45)
        if final_score < 0.45:
            if curr_level == "Dificil":
                curr_level = "Medio"
            elif curr_level == "Medio":
                curr_level = "Facil"
            streak = 0
            
        logger.info(f"Score: {final_score:.2f} | Nueva Dificultad: {curr_level} | Streak: {streak}")
    else:
        logger.info("Última pregunta respondida. No se ajusta dificultad.")

    session["current_difficulty"] = curr_level
    session["streak_correctas"] = streak
    session["current_question"] += 1
    save_session(answer.session_id, session)

    completed = session["current_question"] >= session["total_questions"]
    
    return JSONResponse({
        "success": True,
        "message": "Respuesta recibida.",
        "completed": completed,
        "next_difficulty": curr_level
    })

@app.post("/api/interview/hint")
async def get_hint(payload: HintRequest):
    """Genera una pista para la pregunta actual."""
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
    """Genera feedback detallado sobre la respuesta del usuario."""
    # Pasamos las métricas al servicio de feedback para contextualizar la respuesta
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
    """Genera una explicación detallada de la respuesta correcta."""
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
    """Obtiene la teoría relacionada con la pregunta."""
    explanation = theory_service.get_theory_explanation(payload.get("question"))
    return JSONResponse({"theory": explanation})

@app.get("/results/{session_id}", response_class=HTMLResponse)
async def show_results_page(request: Request, session_id: str):
    """Muestra la página de resultados finales de la entrevista."""
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

    data = {
        "session_id": session_id,
        "total_questions": len(answers),
        "dataset_type": session.get("dataset_type", "squad"),
        "answers": answers
    }
    
    return templates.TemplateResponse("results.html", {"request": request, "data": data})

@app.delete("/api/interview/session/{session_id}")
async def end_interview(session_id: str):
    """Finaliza la sesión de entrevista y limpia los datos temporales."""
    redis_client.delete(f"session:{session_id}")
    redis_client.delete(f"answers:{session_id}")
    redis_client.delete(f"qmap:{session_id}")
    return JSONResponse({"success": True, "message": "Sesión finalizada"})