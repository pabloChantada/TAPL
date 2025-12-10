import os
import logging

try:
    import google.generativeai as genai
except ImportError:
    genai = None
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

class AnswerGenerator:
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
            self.model_name = "deepseek-chat"
            logger.info("🔧 AnswerGenerator configurado con DEEPSEEK")
            
        elif self.provider == "GROQ":
            if not self.api_key_groq:
                raise ValueError("GROQ_API_KEY no configurada.")
            self.client = OpenAI(api_key=self.api_key_groq, base_url="https://api.groq.com/openai/v1")
            self.model_name = "llama-3.3-70b-versatile"
            logger.info("🔧 AnswerGenerator configurado con GROQ")

        else:
            if not self.api_key_gemini:
                raise ValueError("GEMINI_API_KEY no configurada.")
            genai.configure(api_key=self.api_key_gemini)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
            logger.info("🔧 AnswerGenerator configurado con GEMINI")

    def clean_answer(self, raw_answer: str) -> str:
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
            if self.provider in ["DEEPSEEK", "GROQ"]:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                return response.choices[0].message.content.strip()
            else:
                response = self.model.generate_content(prompt)
                return response.text.strip()
        except Exception as e:
            logger.error(f"Error limpiando respuesta con {self.provider}: {e}")
            return raw_answer.strip()

    def generate_hint(self, question: str, correct_answer: str) -> str:
        """
        Genera una pista sutil basada en la pregunta y la respuesta correcta.
        """
        prompt = f"""
        Actúa como un profesor amable. El estudiante está atascado en esta pregunta de entrevista.
        
        PREGUNTA: "{question}"
        RESPUESTA CORRECTA (para tu referencia, NO LA REVELES): "{correct_answer}"
        
        Tu tarea:
        - Da una pista breve (máximo 2 frases).
        - NO des la respuesta directa.
        - Orienta al usuario sobre qué concepto teórico debería recordar o qué fórmula aplicar.
        - Usa un tono alentador.
        """

        try:
            if self.provider in ["DEEPSEEK", "GROQ"]:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7, # Un poco más creativo para las pistas
                    max_tokens=150
                )
                return response.choices[0].message.content.strip()
            else:
                response = self.model.generate_content(prompt)
                return response.text.strip()
        except Exception as e:
            logger.error(f"Error generando pista con {self.provider}: {e}")
            return "Piensa en los conceptos básicos relacionados con el tema de la pregunta."