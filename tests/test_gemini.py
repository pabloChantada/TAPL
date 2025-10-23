# test_gemini_run.py
from project.rag.question_generator import QuestionGenerator, GeminiGenerationError

qg = QuestionGenerator()
try:
    print("Probando generación con prompt de test...")
    q = qg._generate_with_gemini("Contexto de prueba: plantea una pregunta de entrevista basada en este contexto corto.")
    print("Generada:", q)
except GeminiGenerationError as e:
    print("GeminiGenerationError:", e)
except Exception as e:
    print("Error inesperado:", e)

