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

class ExplanationService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "GEMINI").upper()
        self.api_key_gemini = os.getenv("GEMINI_API_KEY")
        self.api_key_deepseek = os.getenv("DEEPSEEK_API_KEY")
        self.api_key_groq = os.getenv("GROQ_API_KEY")
        
        self.client = None
        self.model = None

        if self.provider == "DEEPSEEK":
            if not self.api_key_deepseek:
                raise RuntimeError("DEEPSEEK_API_KEY no configurada.")
            self.client = OpenAI(api_key=self.api_key_deepseek, base_url="https://api.deepseek.com")
            self.model_name = "deepseek-reasoner" 
            logger.info("ExplanationService configurado con DEEPSEEK (Reasoner)")
        
        elif self.provider == "GROQ":
            if not self.api_key_groq:
                raise RuntimeError("GROQ_API_KEY no configurada.")
            self.client = OpenAI(api_key=self.api_key_groq, base_url="https://api.groq.com/openai/v1")
            self.model_name = "llama-3.3-70b-versatile" # Llama 3 es muy bueno razonando
            logger.info("ExplanationService configurado con GROQ")

        else:
            if not self.api_key_gemini:
                raise RuntimeError("GEMINI_API_KEY no configurada.")
            genai.configure(api_key=self.api_key_gemini)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
            logger.info("ExplanationService configurado con GEMINI")

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
            logger.info(f"Generando explicación con {self.provider}...")
            
            if self.provider in ["DEEPSEEK", "GROQ"]:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096,
                    temperature=0.4
                )
                text = response.choices[0].message.content
            else:
                response = self.model.generate_content(
                    prompt,
                    generation_config={"temperature": 0.4, "max_output_tokens": 8192}
                )
                text = response.text

            if not text:
                raise ValueError("Respuesta vacía del LLM")
            return text

        except Exception as e:
            logger.exception(f"Error generando explicación con {self.provider}")
            raise e