from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from project.rag.question_generator import QuestionGenerator, GeminiGenerationError
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


question_generator = QuestionGenerator()

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


@app.post("/api/interview/start")
async def start_interview(session: InterviewSession):
    import uuid

    session_id = str(uuid.uuid4())

    interview_sessions[session_id] = {
        "total_questions": session.total_questions,
        "current_question": 0,
        "started_at": str(os.times()),
    }

    interview_answers[session_id] = []

    return JSONResponse(
        {
            "session_id": session_id,
            "message": "Sesión de entrevista iniciada correctamente",
            "total_questions": session.total_questions,
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
        # Generar UNA SOLA pregunta usando Gemini
        questions = question_generator.generate_interview_questions(num_questions=1)
        generated_question = (
            questions[0] if questions else "Cuéntame sobre tu experiencia profesional."
        )

        return JSONResponse(
            {
                "completed": False,
                "question_number": current_q + 1,
                "total_questions": session["total_questions"],
                "question_text": generated_question,
            }
        )

    except GeminiGenerationError as ge:
        # Respuesta explícita de error si Gemini no pudo generar la pregunta
        return JSONResponse(
            status_code=500,
            content={
                "error": "No fue posible generar la pregunta con Gemini",
                "details": str(ge),
            },
        )
    except Exception as e:
        print(f"Error generating question: {str(e)}")
        # En casos no relacionados con Gemini devolvemos fallback
        return JSONResponse(
            {
                "completed": False,
                "question_number": current_q + 1,
                "total_questions": session["total_questions"],
                "question_text": question_generator._get_fallback_questions(1)[0],
            }
        )


@app.post("/api/interview/answer")
async def save_answer(answer: UserAnswer):
    if answer.session_id not in interview_sessions:
        return JSONResponse(status_code=404, content={"error": "Sesión no encontrada"})

    interview_answers[answer.session_id].append(
        {
            "question_number": answer.question_number,
            "question": answer.question_text,
            "answer": answer.answer_text,
            "timestamp": str(os.times()),
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
            "answers": answers,
        }
    )


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
        ans["question"] for ans in answers
    ]  # Usamos la pregunta como "referencia ideal"

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
        "bleu": bleu_score,
        "rouge": rouge_scores,
        "bertscore": bertscore_avg,
        "answers": answers,
    }

    context = {"request": request, "data": data}
    return templates.TemplateResponse("results.html", context)


@app.delete("/api/interview/session/{session_id}")
async def end_interview(session_id: str):
    if session_id in interview_sessions:
        del interview_sessions[session_id]
    if session_id in interview_answers:
        del interview_answers[session_id]

    return JSONResponse({"success": True, "message": "Sesión finalizada correctamente"})
