from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from project.rag.question_generator import QuestionGenerator, GeminiGenerationError
from project.rag.answer_generator import AnswerGenerator
from project.metrics.feedback_service import FeedbackService
from project.metrics.evaluator import evaluate_full
from project.metrics.explanation_service import ExplanationService
from project.rag.gemini_rag_service import GeminiTheoryService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from .metrics.metrics import Metrics


TOTAL_QUESTIONS = 2
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

# Inicializar con dataset por defecto
question_generator = QuestionGenerator(dataset_type="squad")
answer_generator = AnswerGenerator()
feedback_service = FeedbackService()
explanation_service = ExplanationService()
theory_service = GeminiTheoryService()



# Mount static files
app.mount(
    "/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static"
)


# Models
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


# Temporary storage
interview_sessions = {}
interview_answers = {}
interview_questions = {}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})


@app.get("/api/datasets")
async def get_available_datasets():
    """Endpoint para obtener los datasets disponibles"""
    return JSONResponse(
        {
            "datasets": [
                {
                    "id": "squad",
                    "name": "SQuAD",
                    "description": "Stanford Question Answering Dataset",
                },
                {
                    "id": "natural_questions",
                    "name": "Natural Questions",
                    "description": "Preguntas reales de Google Search",
                },
                {
                    "id": "eli5",
                    "name": "ELI5",
                    "description": "Explain Like I'm 5 (Reddit)",
                },
                {
                    "id": "hotpotqa",
                    "name": "HotpotQA",
                    "description": "Preguntas multi-hop complejas",
                },
                {
                    "id": "coachquant",
                    "name": "CoachQuant",
                    "description": "Preguntas de entrevista cuantitativas",
                }
            ]
        }
    )


@app.post("/api/interview/start")
async def start_interview(session: InterviewSession):
    import uuid

    session_id = str(uuid.uuid4())

    # Cambiar el dataset si es diferente al actual
    if session.dataset_type != question_generator.dataset_type:
        try:
            question_generator.set_dataset(session.dataset_type)
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"No se pudo cargar el dataset '{session.dataset_type}': {str(e)}"
                },
            )

    interview_sessions[session_id] = {
        "total_questions": session.total_questions,
        "current_question": 0,
        "started_at": str(os.times()),
        "dataset_type": session.dataset_type,
    }

    interview_answers[session_id] = []

    return JSONResponse(
        {
            "session_id": session_id,
            "message": "Sesión de entrevista iniciada correctamente",
            "total_questions": session.total_questions,
            "dataset_type": session.dataset_type,
        }
    )


@app.get("/api/interview/question/{session_id}")
async def get_next_question(session_id: str):
    if session_id not in interview_sessions:
        return JSONResponse(status_code=404, content={"error": "Sesión no encontrada"})

    session = interview_sessions[session_id]
    current_q = session["current_question"]

    if current_q >= session["total_questions"]:
        return JSONResponse({"completed": True, "message": "Entrevista completada"})

    try:
        # Generar pregunta + respuesta correcta del dataset
        raw_question, raw_answer = question_generator.generate_single_question_with_answer()

        if raw_question is None:
            raw_question = "No se pudo generar una pregunta."
            raw_answer = ""

        # Limpiar la pregunta (ya viene limpia del question generator)
        question_text = raw_question

        # Limpiar la respuesta correcta usando Gemini
        correct_answer = answer_generator.clean_answer(raw_answer)

        # Guardar en memoria
        if session_id not in interview_questions:
            interview_questions[session_id] = {}

        interview_questions[session_id][current_q + 1] = {
            "question_text": question_text,
            "correct_answer": correct_answer
        }

        return JSONResponse({
            "completed": False,
            "question_number": current_q + 1,
            "total_questions": session["total_questions"],
            "question_text": question_text,
            "correct_answer": correct_answer
        })

    except Exception as e:
        print(f"Error generating question: {str(e)}")
        return JSONResponse(
            {
                "completed": False,
                "question_number": current_q + 1,
                "question_text": "Error generando pregunta.",
            }
        )


@app.post("/api/interview/answer")
async def save_answer(answer: UserAnswer):
    if answer.session_id not in interview_sessions:
        return JSONResponse(status_code=404, content={"error": "Sesión no encontrada"})

    correct_answer = interview_questions[answer.session_id][answer.question_number]["correct_answer"]

    interview_answers[answer.session_id].append(
        {
            "question_number": answer.question_number,
            "question": answer.question_text,
            "answer": answer.answer_text,
            "correct_answer": correct_answer,
            "timestamp": str(os.times()),
            "feedback": None,
            "explanation": None
        }
    )


    session = interview_sessions[answer.session_id]
    session["current_question"] += 1

    if session["current_question"] >= session["total_questions"]:
        return JSONResponse(
            {
                "success": True,
                "message": "Respuesta guardada correctamente",
                "completed": True,
                "final_message": "Entrevista completada",
            }
        )

    return JSONResponse(
        {
            "success": True,
            "message": "Respuesta guardada correctamente",
            "completed": False,
        }
    )


@app.get("/api/interview/results/{session_id}")
async def get_results(session_id: str):
    if session_id not in interview_sessions:
        return JSONResponse(status_code=404, content={"error": "Sesión no encontrada"})

    answers = interview_answers.get(session_id, [])

    return JSONResponse(
        {
            "session_id": session_id,
            "total_questions": interview_sessions[session_id]["total_questions"],
            "dataset_type": interview_sessions[session_id].get("dataset_type", "squad"),
            "answers": answers,
        }
    )

@app.post("/api/feedback")
async def generate_feedback(payload: dict):
    logger.info("🔵 [API] /api/feedback llamado")

    question = payload.get("question")
    correct_answer = payload.get("correct_answer")
    user_answer = payload.get("user_answer")
    evaluation = payload.get("evaluation")

    logger.info(f"📝 Pregunta recibida: {question[:120]}...")
    logger.info(f"🟢 Correct Answer Length: {len(correct_answer)}")
    logger.info(f"🟣 User Answer Length: {len(user_answer)}")
    logger.info(f"📊 Evaluation: {evaluation}")

    if not all([question, correct_answer, user_answer, evaluation]):
        logger.error("❌ Campos faltantes en /api/feedback")
        return JSONResponse(
            status_code=400,
            content={"error": "Faltan campos para generar feedback"}
        )

    try:
        logger.info("⚙️ Llamando a FeedbackService.generate_feedback()...")
        feedback = feedback_service.generate_feedback(
            question=question,
            correct_answer=correct_answer,
            user_answer=user_answer,
            evaluation=evaluation
        )
        logger.info("✅ Feedback generado correctamente")

        return JSONResponse({"feedback": feedback})

    except Exception as e:
        logger.exception("🔥 ERROR crítico generando feedback")
        return JSONResponse(
            status_code=500,
            content={"error": f"No se pudo generar feedback: {str(e)}"}
        )
    
@app.post("/api/explanation")
async def generate_explanation(payload: dict):
    logger.info("🔵 [API] /api/explanation llamado")

    question = payload.get("question")
    correct_answer = payload.get("correct_answer")
    session_id = payload.get("session_id")
    question_number = payload.get("question_number")

    # Validación
    if not all([question, correct_answer, session_id, question_number]):
        return JSONResponse(status_code=400, content={"error": "Faltan campos"})

    # Buscar respuesta guardada
    saved_answer = next(
        (a for a in interview_answers.get(session_id, [])
         if a["question_number"] == question_number),
        None
    )

    if saved_answer is None:
        return JSONResponse(status_code=404, content={"error": "Respuesta no encontrada"})

    # Ya existe → devolver cache
    if saved_answer["explanation"] is not None:
        logger.info("♻️ Explicación ya existente — devolviendo cache")
        return JSONResponse({"explanation": saved_answer["explanation"]})

    # NO existe → generar con Gemini
    try:
        explanation = explanation_service.generate_explanation(
            question=question,
            correct_answer=correct_answer
        )
    except Exception as e:
        logger.exception("ERROR generando explicación")
        return JSONResponse(status_code=500, content={"error": str(e)})

    # Guardar
    saved_answer["explanation"] = explanation
    logger.info("💾 Explicación guardada correctamente")

    return JSONResponse({"explanation": explanation})

@app.post("/api/theory")
async def get_theory(payload: dict):
    question = payload.get("question")
    if not question:
        return JSONResponse(status_code=400, content={"error": "Falta la pregunta"})
        
    explanation = theory_service.get_theory_explanation(question)
    return JSONResponse({"theory": explanation})

    
@app.get("/results/{session_id}", response_class=HTMLResponse)
async def show_results_page(request: Request, session_id: str):
    if session_id not in interview_sessions:
        return HTMLResponse(content="<h1>Sesión no encontrada</h1>", status_code=404)

    answers = interview_answers.get(session_id, [])
    if not answers:
        return HTMLResponse(
            content="<h1>No hay respuestas para evaluar</h1>", status_code=400
        )

    # Extraer respuestas y preguntas esperadas (fallback si no hay preguntas guardadas)
    predictions = [ans["answer"] for ans in answers]
    references = [
    ans["correct_answer"] for ans in answers
    ]
    evaluations = []
    for ans in answers:
        evaluation = evaluate_full(
            correct_answer=ans["correct_answer"],
            user_answer=ans["answer"]
        )   
        evaluations.append(evaluation)

    # Calcular métricas
    metrics = Metrics()
    bleu_score = round(metrics.bleu(predictions, references), 4)
    rouge_scores = {
        k: round(v, 4) for k, v in metrics.rouge(predictions, references).items()
    }
    bertscore_avg = round(metrics.bertscore(predictions, references, lang="es"), 4)

    # Preparar data para el template
    data = {
        "session_id": session_id,
        "total_questions": len(answers),
        "dataset_type": interview_sessions[session_id].get("dataset_type", "squad"),
        "bleu": bleu_score,
        "rouge": rouge_scores,
        "bertscore": bertscore_avg,
        "answers": answers,
        "evaluations": evaluations 
    }

    context = {"request": request, "data": data}
    return templates.TemplateResponse("results.html", context)


@app.delete("/api/interview/session/{session_id}")
async def end_interview(session_id: str):
    if session_id in interview_sessions:
        del interview_sessions[session_id]
    if session_id in interview_answers:
        del interview_answers[session_id]
    if session_id in interview_questions:
        del interview_questions[session_id]


    return JSONResponse({"success": True, "message": "Sesión finalizada correctamente"})
