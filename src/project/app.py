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
from project.metrics.evaluator import evaluate_full
from project.metrics.explanation_service import ExplanationService
from project.rag.gemini_rag_service import GeminiTheoryService
from project.metrics.metrics import Metrics

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
    # Fallback simple para desarrollo si Redis falla
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
# (Estos servicios ya leen internamente LLM_PROVIDER para elegir Gemini o DeepSeek)
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
    total_questions: int = TOTAL_QUESTIONS
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
    Tarea que se ejecuta en segundo plano.
    Calcula las métricas pesadas y actualiza el registro en Redis.
    """
    logger.info(f"[Background] Iniciando evaluación para sesión {session_id} - P{question_number}")
    try:
        # 1. Cálculo pesado (BERTScore, etc.)
        evaluation = evaluate_full(
            correct_answer=correct_answer,
            user_answer=user_answer
        )
        
        # 2. Actualizar Redis (Leemos, modificamos, guardamos)
        # Nota: En un sistema muy concurrido, esto requeriría locks, pero para este caso sirve.
        answers = get_answers(session_id)
        updated = False
        for ans in answers:
            if ans["question_number"] == question_number:
                ans["evaluation"] = evaluation
                updated = True
                break
        
        if updated:
            save_answers(session_id, answers)
            logger.info(f"[Background] Evaluación guardada para P{question_number}")
        else:
            logger.warning(f"[Background] No se encontró la respuesta para actualizar en sesión {session_id}")

    except Exception as e:
        logger.error(f"[Background] Error en evaluación: {e}")

# --- ENDPOINTS ---

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})

@app.get("/api/datasets")
async def get_available_datasets():
    return JSONResponse({
        "datasets": [
            {"id": "squad", "name": "SQuAD", "description": "Stanford Question Answering Dataset"},
            # {"id": "natural_questions", "name": "Natural Questions", "description": "Preguntas reales de Google Search"},
            # {"id": "eli5", "name": "ELI5", "description": "Explain Like I'm 5 (Reddit)"},
            # {"id": "hotpotqa", "name": "HotpotQA", "description": "Preguntas multi-hop complejas"},
            {"id": "coachquant", "name": "CoachQuant", "description": "Preguntas de entrevista cuantitativas"}
        ]
    })

@app.post("/api/interview/start")
async def start_interview(session: InterviewSession):
    session_id = str(uuid.uuid4())

    # Configurar dataset
    if session.dataset_type != question_generator.dataset_type:
        try:
            question_generator.set_dataset(session.dataset_type)
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    # Inicializar estado en Redis
    session_data = {
        "total_questions": session.total_questions,
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
        # Generación
        raw_question, raw_answer = question_generator.generate_single_question_with_answer()
        if not raw_question:
            raw_question, raw_answer = "Error generando pregunta.", ""

        # Limpieza (usa Gemini o DeepSeek según config)
        clean_question = raw_question # Ya viene limpia del generator
        clean_answer = answer_generator.clean_answer(raw_answer)

        # Guardar mapeo de pregunta actual
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
    """
    Guarda la respuesta y lanza el cálculo de métricas en background.
    """
    session = get_session(answer.session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Sesión no encontrada"})

    # Recuperar respuesta correcta
    q_map = get_questions_map(answer.session_id)
    q_data = q_map.get(str(answer.question_number))
    if not q_data:
        return JSONResponse(status_code=400, content={"error": "Datos de pregunta perdidos"})

    # Objeto respuesta (sin evaluación aún)
    new_answer = {
        "question_number": answer.question_number,
        "question": answer.question_text,
        "answer": answer.answer_text,
        "correct_answer": q_data["correct_answer"],
        "timestamp": str(os.times()),
        "feedback": None,
        "explanation": None,
        "evaluation": None # Se llenará en background
    }

    # Guardar en Redis
    answers_list = get_answers(answer.session_id)
    answers_list.append(new_answer)
    save_answers(answer.session_id, answers_list)

    # Avanzar sesión
    session["current_question"] += 1
    save_session(answer.session_id, session)

    # LANZAR BACKGROUND TASK
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
        "message": "Respuesta recibida. Evaluando en segundo plano.",
        "completed": completed
    })

@app.post("/api/interview/hint")
async def get_hint(payload: HintRequest):
    session_id = payload.session_id
    
    # Validaciones básicas
    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Sesión no encontrada"})
    
    # Recuperar la pregunta actual de la "base de datos" en memoria/redis
    # Nota: Si usas Redis, asegúrate de usar get_questions_map(session_id)
    # Si estás en local con workers=1 (memoria), usa el diccionario:
    
    # Lógica compatible con ambos (Redis/Memoria según tu configuración actual):
    try:
        q_map = get_questions_map(session_id)
        q_data = q_map.get(str(payload.question_number))

        if not q_data:
            return JSONResponse(status_code=400, content={"error": "Pregunta no encontrada"})

        # Generar la pista
        hint = answer_generator.generate_hint(
            question=q_data["question_text"], 
            correct_answer=q_data["correct_answer"]
        )
        
        return JSONResponse({"hint": hint})

    except Exception as e:
        logger.error(f"Error en endpoint hint: {e}")
        return JSONResponse(status_code=500, content={"error": "Error generando pista"})

@app.get("/api/interview/results/{session_id}")
async def get_results_api(session_id: str):
    session = get_session(session_id)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Sesión no encontrada"})
    
    answers = get_answers(session_id)
    return JSONResponse({
        "session_id": session_id,
        "total_questions": session["total_questions"],
        "answers": answers
    })

@app.post("/api/feedback")
async def generate_feedback(payload: dict):
    # Llama al servicio (que ya sabe si usar DeepSeek o Gemini)
    try:
        feedback = feedback_service.generate_feedback(
            payload.get("question"),
            payload.get("correct_answer"),
            payload.get("user_answer"),
            payload.get("evaluation")
        )
        return JSONResponse({"feedback": feedback})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/explanation")
async def generate_explanation(payload: dict):
    session_id = payload.get("session_id")
    question_number = payload.get("question_number")
    
    # Intentar buscar en cache (Redis)
    answers = get_answers(session_id)
    target_ans = next((a for a in answers if a["question_number"] == question_number), None)
    
    if target_ans and target_ans.get("explanation"):
        return JSONResponse({"explanation": target_ans["explanation"]})

    # Generar
    try:
        explanation = explanation_service.generate_explanation(
            payload.get("question"),
            payload.get("correct_answer")
        )
        
        # Guardar en cache si es posible
        if target_ans:
            target_ans["explanation"] = explanation
            save_answers(session_id, answers)
            
        return JSONResponse({"explanation": explanation})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/api/theory")
async def get_theory(payload: dict):
    # Este servicio maneja su propio error si está en modo DeepSeek
    explanation = theory_service.get_theory_explanation(payload.get("question"))
    return JSONResponse({"theory": explanation})

@app.get("/results/{session_id}", response_class=HTMLResponse)
async def show_results_page(request: Request, session_id: str):
    session = get_session(session_id)
    if not session:
        return HTMLResponse("<h1>Sesión no encontrada</h1>", status_code=404)

    answers = get_answers(session_id)
    
    # Preparar métricas globales
    # Si alguna evaluación aún es None (background task lenta), calculamos on-the-fly o ponemos 0
    predictions = []
    references = []
    evaluations = []
    
    for ans in answers:
        ev = ans.get("evaluation")
        if not ev:
            # Fallback síncrono si el usuario fue muy rápido viendo resultados
            ev = evaluate_full(ans["correct_answer"], ans["answer"])
            ans["evaluation"] = ev # Actualizamos localmente para mostrar
        
        evaluations.append(ev)
        predictions.append(ans["answer"])
        references.append(ans["correct_answer"])

    metrics = Metrics()
    try:
        bleu = round(metrics.bleu(predictions, references), 4)
        rouge = {k: round(v, 4) for k, v in metrics.rouge(predictions, references).items()}
        bertscore = round(metrics.bertscore(predictions, references, lang="es"), 4)
    except Exception:
        bleu, rouge, bertscore = 0, {}, 0

    data = {
        "session_id": session_id,
        "total_questions": len(answers),
        "dataset_type": session.get("dataset_type", "squad"),
        "bleu": bleu,
        "rouge": rouge,
        "bertscore": bertscore,
        "answers": answers,
        "evaluations": evaluations
    }
    
    return templates.TemplateResponse("results.html", {"request": request, "data": data})

@app.delete("/api/interview/session/{session_id}")
async def end_interview(session_id: str):
    redis_client.delete(f"session:{session_id}")
    redis_client.delete(f"answers:{session_id}")
    redis_client.delete(f"qmap:{session_id}")
    return JSONResponse({"success": True, "message": "Sesión finalizada"})