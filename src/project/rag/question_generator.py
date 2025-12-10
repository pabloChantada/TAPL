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
            self.model_name = "llama-3.3-70b-versatile" 
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

    def generate_interview_questions(self, num_questions: int = 5) -> List[str]:
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
            except Exception:
                return text.strip()
        return text.strip()

    def _extract_dataset_answer(self, text: str) -> str:
        if "Respuesta:" in text:
            try:
                return text.split("Respuesta:")[1].strip()
            except Exception:
                return ""
        return ""

    def normalize_question_with_llm(self, raw_question: str) -> str:
        prompt = f"""
        Eres un experto en matemáticas y entrevistas técnicas.
        Vas a recibir una pregunta original escrita en inglés y posiblemente con LaTeX roto.

        Tu tarea es:
        - Convertir expresiones LaTeX a matemáticas Unicode legibles (x², √5, π, ⅓, etc.) cuando sea posible sin perder precisión, o usar LaTeX limpio.
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

    def _classify_answer_difficulty(self, question: str, answer: str) -> str:
        """
        Usa el LLM para determinar la dificultad real basada en conceptos, no en longitud.
        """
        prompt = f"""
        Eres un experto en entrevistas cuantitativas (Quant Finance) y de programación.
        Analiza la siguiente pregunta y su respuesta para clasificar su dificultad.

        Pregunta: {question}
        Respuesta: {answer}

        Clasifica la dificultad CONCEPTUAL para un candidato junior en una de estas 3 categorías:
        - Facil: Cálculo directo, definiciones básicas, aritmética simple, lógica de sentido común.
        - Medio: Requiere formular ecuaciones lineales, probabilidad condicional estándar, algoritmos conocidos o pasos múltiples.
        - Dificil: Requiere intuición profunda, cálculo estocástico, combinatoria avanzada (simetrías), programación dinámica o pensamiento lateral complejo.

        Responde SOLAMENTE con una palabra: "Facil", "Medio" o "Dificil".
        """

        try:
            content = ""
            if self.provider in ["DEEPSEEK", "GROQ"]:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=10
                )
                content = response.choices[0].message.content.strip()
            else:
                response = self.model.generate_content(prompt)
                content = response.text.strip()
            
            # Limpieza básica de la respuesta
            difficulty = content.replace("á", "a").replace("í", "i").replace("cil", "cil").split()[0].title()
            
            valid_levels = ["Facil", "Medio", "Dificil"]
            if difficulty not in valid_levels:
                # Fallback si el modelo se pone creativo
                logger.warning(f"Clasificación desconocida '{difficulty}', usando Medio.")
                return "Medio"
                
            return difficulty

        except Exception as e:
            logger.error(f"Error clasificando dificultad: {e}")
            return "Medio" # Fallback seguro

    def generate_single_question_with_answer(self, target_difficulty: str = "Facil"):
        # Leemos un batch pequeño para no saturar, pero suficiente para encontrar variedad
        # NOTA: En producción, idealmente esto se pre-calcula y se filtra por metadatos DB.
        contexts = self.rag.read_dataset(max_texts=10, sample_random=True)
        
        best_candidate = None
        levels = ["Facil", "Medio", "Dificil"]

        def dist(a, b):
            return abs(levels.index(a) - levels.index(b))

        # Iteramos sobre los contextos recuperados
        for i, ctx in enumerate(contexts):
            raw_question = self._extract_dataset_question(ctx)
            correct_answer = self._extract_dataset_answer(ctx)
            
            if not raw_question or not correct_answer:
                continue
            
            # Clasificamos con LLM (Ojo: esto hace llamadas API en bucle, limitamos con el break)
            detected = self._classify_answer_difficulty(raw_question, correct_answer)
            logger.info(f"Pregunta analizada: {detected} (Target: {target_difficulty})")

            # Si encontramos match exacto, normalizamos y devolvemos
            if detected == target_difficulty:
                clean_question = self.normalize_question_with_llm(raw_question)
                return clean_question, correct_answer, detected

            # Si no, guardamos el mejor candidato por si acaso no encontramos el exacto
            if (best_candidate is None) or dist(detected, target_difficulty) < dist(best_candidate[2], target_difficulty):
                best_candidate = (raw_question, correct_answer, detected)
            
            # Optimización: Si ya hemos mirado 3 y no encontramos match, paramos para no tardar mucho
            if i >= 3 and best_candidate:
                break

        if best_candidate:
            raw_question, correct_answer, detected = best_candidate
            clean_question = self.normalize_question_with_llm(raw_question)
            # Retornamos lo que encontramos, aunque no sea el target exacto
            return clean_question, correct_answer, detected

        # Fallback total
        return None, None, target_difficulty