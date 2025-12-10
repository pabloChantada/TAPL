import os
from typing import List, Optional
import logging
from .rag import RAG

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

class LLMGenerationError(Exception):
    pass

class QuestionGenerator:
    def __init__(self, dataset_type: str = "squad"):
        self.dataset_type = dataset_type
        self.rag = RAG(dataset_type=dataset_type)
        try:
            self.rag.load_chroma_db()
        except Exception as e:
            logger.error(f"[QuestionGenerator] No se pudo cargar chroma DB en init: {e}")

        # --- CONFIGURACIÓN DEL PROVEEDOR ---
        self.provider = os.getenv("LLM_PROVIDER", "GEMINI").upper()
        self.api_key_gemini = os.getenv("GEMINI_API_KEY")
        self.api_key_deepseek = os.getenv("DEEPSEEK_API_KEY")
        self.api_key_groq = os.getenv("GROQ_API_KEY")
        
        self.client = None
        self.model = None

        if self.provider == "DEEPSEEK":
            if not self.api_key_deepseek:
                raise LLMGenerationError("DEEPSEEK_API_KEY no configurada.")
            self.client = OpenAI(api_key=self.api_key_deepseek, base_url="https://api.deepseek.com")
            self.model_name = "deepseek-chat"
            logger.info("🔧 QuestionGenerator configurado con DEEPSEEK")
            
        elif self.provider == "GROQ":
            if not self.api_key_groq:
                raise LLMGenerationError("GROQ_API_KEY no configurada.")
            self.client = OpenAI(api_key=self.api_key_groq, base_url="https://api.groq.com/openai/v1")
            self.model_name = "llama-3.3-70b-versatile" # Modelo potente y gratuito en Groq
            logger.info("🔧 QuestionGenerator configurado con GROQ")

        else: # Default to GEMINI
            if not self.api_key_gemini:
                raise LLMGenerationError("GEMINI_API_KEY no configurada.")
            genai.configure(api_key=self.api_key_gemini)
            self.model = genai.GenerativeModel("gemini-2.5-flash")
            logger.info("🔧 QuestionGenerator configurado con GEMINI")


    def set_dataset(self, dataset_type: str):
        if dataset_type != self.dataset_type:
            self.dataset_type = dataset_type
            self.rag = RAG(dataset_type=dataset_type)
            try:
                self.rag.load_chroma_db()
                logger.info(f"[QuestionGenerator] Dataset cambiado a: {dataset_type}")
            except Exception as e:
                logger.error(f"[QuestionGenerator] Error cargando dataset '{dataset_type}': {e}")

    def generate_interview_questions(self, num_questions: int = 5, topic: str = "") -> List[str]:
        try:
            contexts = self.rag.read_dataset(max_texts=num_questions * 4, sample_random=True)
            questions = []
            used_contexts = set()

            for context in contexts:
                if len(questions) >= num_questions:
                    break
                snippet = context[:150]
                if snippet in used_contexts:
                    continue
                used_contexts.add(snippet)

                raw_question = self._extract_dataset_question(context)
                clean_question = self.normalize_question_with_llm(raw_question)
                questions.append(clean_question)

            return questions[:num_questions]
        except Exception as e:
            logger.error(f"Error generando preguntas: {str(e)}")
            return []

    def _extract_dataset_question(self, text: str) -> str:
        if "Pregunta:" in text:
            try:
                return text.split("Pregunta:")[1].split("Respuesta:")[0].strip()
            except:
                return text.strip()
        return text.strip()

    def _extract_dataset_answer(self, text: str) -> str:
        if "Respuesta:" in text:
            try:
                return text.split("Respuesta:")[1].strip()
            except:
                return ""
        return ""

    def normalize_question_with_llm(self, raw_question: str) -> str:
        prompt = f"""
        Eres un experto en matemáticas.
        Vas a recibir una pregunta original escrita en inglés y posiblemente con LaTeX roto.

        Tu tarea es:
        - Convertir expresiones LaTeX a matemáticas Unicode legibles (x², √5, π, ⅓, etc.)
        - Quitar los símbolos $.
        - Corregir el texto.
        - Traducir al español.
        - No inventes contenido.
        - Devuelve solo la pregunta final.

        Pregunta original:
        {raw_question}
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
            logger.error(f"Error normalizando pregunta con {self.provider}: {e}")
            return raw_question

    def normalize_question_with_gemini(self, raw_question: str) -> str:
        return self.normalize_question_with_llm(raw_question)

    def generate_single_question_with_answer(self):
        contexts = self.rag.read_dataset(max_texts=10, sample_random=True)
        for ctx in contexts:
            raw_question = self._extract_dataset_question(ctx)
            correct_answer = self._extract_dataset_answer(ctx)
            clean_question = self.normalize_question_with_llm(raw_question)
            return clean_question, correct_answer
        return None, None