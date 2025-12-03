from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from project.rag.question_generator import QuestionGenerator, GeminiGenerationError
from project.rag.answer_generator import AnswerGenerator

from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from .metrics.metrics import Metrics


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
    total_questions: int = 2 # Default to 2 questions
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


@app.get("/results/{session_id}", response_class=HTMLResponse)
async def show_results_page(request: Request, session_id: str):
    print(f"[DEBUG] Cargando resultados para session_id: {session_id}")
    print(f"[DEBUG] Sesiones activas: {list(interview_sessions.keys())}")
    
    if session_id not in interview_sessions:
        print(f"[ERROR] Sesión {session_id} no encontrada")
        return HTMLResponse(content="<h1>Sesión no encontrada</h1>", status_code=404)

    answers = interview_answers. get(session_id, [])
    print(f"[DEBUG] Número de respuestas encontradas: {len(answers)}")
    
    if not answers:
        return HTMLResponse(
            content="<h1>No hay respuestas para evaluar</h1>", status_code=400
        )

    # Extraer respuestas del usuario y respuestas correctas
    predictions = [ans["answer"] for ans in answers]
    
    # Manejar correctamente el caso donde correct_answer puede no existir
    references = []
    for ans in answers:
        correct = ans. get("correct_answer", "")
        if not correct:
            # Fallback: buscar en interview_questions
            q_num = ans["question_number"]
            if session_id in interview_questions and q_num in interview_questions[session_id]:
                correct = interview_questions[session_id][q_num]. get("correct_answer", "No disponible")
            else:
                correct = "No disponible"
        references.append(correct)

    # Calcular métricas
    try:
        metrics = Metrics()
        bleu_score = round(float(metrics.bleu(predictions, references)), 4)
        
        # Convertir valores NumPy a float nativos de Python
        rouge_raw = metrics.rouge(predictions, references)
        rouge_scores = {
            k: round(float(v), 4) for k, v in rouge_raw.items()
        }
        
        bertscore_avg = round(float(metrics.bertscore(predictions, references, lang="es")), 4)
        
        print(f"[DEBUG] BLEU: {bleu_score}")
        print(f"[DEBUG] ROUGE: {rouge_scores}")
        print(f"[DEBUG] BERTScore: {bertscore_avg}")
        
    except Exception as e:
        print(f"[ERROR] Error calculating metrics: {str(e)}")
        import traceback
        traceback.print_exc()
        # Valores por defecto en caso de error
        bleu_score = 0.0
        rouge_scores = {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0, "rougeLsum": 0.0}
        bertscore_avg = 0.0

    # Preparar data para el template - asegurando que correct_answer esté presente
    enriched_answers = []
    for i, ans in enumerate(answers):
        enriched_ans = ans.copy()
        if "correct_answer" not in enriched_ans or not enriched_ans["correct_answer"]:
            enriched_ans["correct_answer"] = references[i]
        enriched_answers.append(enriched_ans)

    data = {
        "session_id": session_id,
        "total_questions": len(answers),
        "dataset_type": interview_sessions[session_id]. get("dataset_type", "squad"),
        "bleu": bleu_score,
        "rouge": rouge_scores,
        "bertscore": bertscore_avg,
        "answers": enriched_answers,
    }

    print(f"[DEBUG] Data preparada para template: {data}")

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
