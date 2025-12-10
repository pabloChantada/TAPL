import os
import logging

try:
    import google.generativeai as genai
except ImportError:
    pass
try:
    from openai import OpenAI
except ImportError:
    pass

logger = logging.getLogger(__name__)

class FeedbackService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "GEMINI").upper()
        self.api_key_gemini = os.getenv("GEMINI_API_KEY")
        self.api_key_deepseek = os.getenv("DEEPSEEK_API_KEY")
        self.api_key_groq = os.getenv("GROQ_API_KEY")
        
        self.client = None
        self.model = None

        if self.provider == "DEEPSEEK":
            if not self.api_key_deepseek:
                raise ValueError("DEEPSEEK_API_KEY no configurada.")
            self.client = OpenAI(api_key=self.api_key_deepseek, base_url="https://api.deepseek.com")
            self.model_name = "deepseek-reasoner"
            logger.info("FeedbackService configurado con DEEPSEEK (Reasoner)")
            self._warm_up_client()
        
        elif self.provider == "GROQ":
            if not self.api_key_groq:
                raise ValueError("GROQ_API_KEY no configurada.")
            self.client = OpenAI(api_key=self.api_key_groq, base_url="https://api.groq.com/openai/v1")
            self.model_name = "llama-3.3-70b-versatile"
            logger.info("FeedbackService configurado con GROQ")
            self._warm_up_client()

        else:
            if not self.api_key_gemini:
                raise ValueError("GEMINI_API_KEY no configurada.")
            genai.configure(api_key=self.api_key_gemini)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
            logger.info("🔧 FeedbackService configurado con GEMINI")
            try:
                self.model.generate_content("Hi")
            except Exception as e:
                logger.warning(f"Gemini warm-up failed: {e}")

    def _warm_up_client(self):
        try:
            self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
        except Exception as e:
            logger.warning(f"{self.provider} warm-up failed: {e}")

    def generate_feedback(self, question, correct_answer, user_answer, evaluation):
        prompt = f"""
Eres un evaluador experto de entrevistas cuantitativas.
Tu tarea es analizar la respuesta del usuario de forma breve y directa.
NO resuelvas el problema, NO des la solución paso a paso.

Genera un feedback conciso que incluya únicamente:
- Un análisis breve de la respuesta del usuario.
- Qué partes son correctas y qué falta.
- Recomendación de mejora.

NO uses formato de secciones ni listas largas.  
Responde en un texto fluido y compacto de no más de 8–10 líneas en español.

---

PREGUNTA:
{question}

RESPUESTA CORRECTA:
{correct_answer}

RESPUESTA DEL USUARIO:
{user_answer}

METRICAS:
{evaluation}

Genera el feedback AHORA en español.
"""
        try:
            logger.info(f"Generando feedback con {self.provider}...")
            
            if self.provider in ["DEEPSEEK", "GROQ"]:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=4096
                )
                text = response.choices[0].message.content
            else:
                response = self.model.generate_content(
                    prompt,
                    generation_config={"temperature": 0.4, "max_output_tokens": 8192}
                )
                if response.candidates and response.candidates[0].content.parts:
                    text = response.candidates[0].content.parts[0].text
                else:
                    text = ""

            if not text:
                return "No se pudo generar feedback."
            return text

        except Exception as e:
            logger.exception(f"Error generando feedback con {self.provider}")
            return "Ocurrió un error generando el feedback."