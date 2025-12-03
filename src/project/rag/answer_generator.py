import os
from typing import Optional

class GeminiGenerationError(Exception):
    pass


class AnswerGenerator:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise GeminiGenerationError("GEMINI_API_KEY no está configurada.")

        import google.generativeai as genai
        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel("gemini-2.5-flash")


    def clean_answer(self, raw_answer: str) -> str:
        """
        Limpieza + traducción de la respuesta correcta del dataset.
        Mantiene precisión matemática.
        """
        prompt = f"""
        Eres un asistente experto en matemáticas.
        Recibirás una respuesta original extraída de un dataset, probablemente
        escrita en inglés y con notación LaTeX o símbolos como $...$.

        Tareas:
        - Elimina todos los símbolos $ del texto.
        - Corrige cualquier expresión LaTeX rota.
        - Convierte expresiones matemáticas a Unicode claro (x², √5, π, ⅓…).
        - No alteres el significado matemático.
        - No inventes información nueva.
        - Si la respuesta incluye pasos explicativos, mantenlos.
        - Traduce la respuesta final al español.
        - Devuelve únicamente la respuesta limpia.

        Respuesta original:
        {raw_answer}
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print("Error limpiando respuesta:", e)
            return raw_answer.strip()
