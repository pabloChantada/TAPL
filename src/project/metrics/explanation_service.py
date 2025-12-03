import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)


class ExplanationService:
    """
    Genera una explicación paso a paso del razonamiento correcto
    basado únicamente en la respuesta oficial del dataset.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY no está configurada.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def generate_explanation(self, question, correct_answer):
        prompt = f"""
Eres un profesor experto en matemáticas y estadística.

Tu tarea es generar **una explicación paso a paso**, breve, clara y ordenada,
que explique cómo resolver correctamente el problema basándote ÚNICAMENTE
en la respuesta oficial.

NO inventes pasos nuevos, NO cambies el razonamiento oficial.

---

PREGUNTA:
{question}

RESPUESTA OFICIAL:
{correct_answer}

---

Genera AHORA una explicación paso a paso, concisa y entendible.
"""

        try:
            logger.info("🟡 Llamando a Gemini para explicación…")
            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.4, "max_output_tokens": 8192}
            )
            text = response.text
            if not text:
                raise ValueError("Gemini devolvió una respuesta vacía")
            return text

        except Exception as e:
            logger.exception("❌ Error generando explicación")
            raise e
