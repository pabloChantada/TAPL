import os
from google import genai
from google.genai import types
import logging
logger = logging.getLogger(__name__)

class GeminiGenerationError(Exception):
    pass
class FeedbackService:
    """
    Servicio para generar feedback explicativo basado en LLM (Gemini).
    Recibe la pregunta, la respuesta correcta, la del usuario y las métricas heurísticas.
    Devuelve un feedback estructurado en español.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise GeminiGenerationError("GEMINI_API_KEY no está configurada.")

        import google.generativeai as genai
        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel("gemini-2.5-flash")

        # 🔥 PRECALENTAR EL MODELO PARA EVITAR BLOQUEO EN LA PRIMERA REQUEST
        try:
            self.model.generate_content(
                "Hello. This is a system warm-up request. Respond with 'OK'."
            )
        except Exception as e:
            print("[Warning] Warm-up request failed:", e)

    def generate_feedback(self, question, correct_answer, user_answer, evaluation):

        logger.info("📏 Tamaños del prompt:")
        logger.info(f"   Pregunta: {len(question)} chars")
        logger.info(f"   Correct Answer: {len(correct_answer)} chars")
        logger.info(f"   User Answer: {len(user_answer)} chars")

        prompt = f"""
Eres un evaluador experto de entrevistas cuantitativas.
Tu tarea es analizar la respuesta del usuario de forma breve y directa.
NO resuelvas el problema, NO des la solución paso a paso y NO reproduzcas la respuesta correcta completa.

Genera un feedback conciso que incluya únicamente:
- Un análisis breve de la respuesta del usuario.
- Qué partes, si alguna, son correctas.
- Qué partes faltan o están mal razonadas.
- Errores conceptuales o numéricos relevantes.
- Una recomendación de mejora clara y corta.

NO uses formato de secciones, listas largas o títulos.  
Responde en un texto fluido y compacto de no más de 8–10 líneas.  
Evita el markdown y evita enumeraciones.  
Habla de manera natural, como si dieras feedback rápido de un profesor a un alumno.

---

PREGUNTA:
{question}

RESPUESTA CORRECTA (referencia interna):
{correct_answer}

RESPUESTA DEL USUARIO:
{user_answer}

EVALUACIÓN AUTOMÁTICA:
- Similitud semántica: {evaluation["semantic_similarity"]:.3f}
- Validación numérica: {evaluation["numeric_score"]}
- Keyword coverage: {evaluation["keyword_coverage"]:.3f}
- Reasoning structure: {evaluation["reasoning_structure"]:.3f}
- Score final: {evaluation["final_score"]:.3f}

---

Genera el feedback AHORA en español.
"""


        logger.info(f"🧾 Longitud final del PROMPT: {len(prompt)} chars")

        try:
            logger.info("🟡 Enviando prompt a Gemini...")
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.4,
                    "max_output_tokens": 8192,
                }
            )

            logger.info("🟢 Respuesta RAW de Gemini:")
            logger.info(response)

            # 🔍 Validación de seguridad: ¿hay contenido real?
            if (not response.candidates
                or not response.candidates[0].content
                or not response.candidates[0].content.parts):
                
                finish = response.candidates[0].finish_reason if response.candidates else "n/a"
                logger.error(f"❌ Gemini NO devolvió texto. finish_reason={finish}")

                return (
                    "### Feedback no disponible\n"
                    "El modelo no pudo generar un feedback válido. "
                    "Esto suele ocurrir cuando la respuesta del usuario es demasiado corta, "
                    "vacía o no interpretable."
                )

            # ✔️ Texto válido garantizado
            text = response.candidates[0].content.parts[0].text
            return text

        except Exception as e:
            logger.exception("🔥 Error llamando a Gemini")
            return "Ocurrió un error generando el feedback."
