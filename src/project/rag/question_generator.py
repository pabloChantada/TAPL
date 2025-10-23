
import os
import random
import logging
from typing import List, Optional
from .rag import RAG
from google import genai

class GeminiGenerationError(Exception):
    pass

class QuestionGenerator:
    def __init__(self):
        self.rag = RAG()
        try:
            self.rag.load_chroma_db()
        except Exception as e:
            print(f"[QuestionGenerator] No se pudo cargar chroma DB en init: {e}")

        self.question_template = """
        Eres un experto examinador. Genera **UNA UNICA PREGUNTA** para evaluar a un usuario.
        Es un sistema de entrevistas, tu función es devolver **ÚNICAMENTE LA PREGUNTA** dado un contexto.
        La pregunta no debe superar los 100 caracteres y debe ser en **ESPAÑOL**. El contexto que vas a utilizar es: {context}
        """    
    def generate_interview_questions(self, num_questions: int = 5, topic: str = "") -> List[str]:
        try:
            contexts: List[str] = []
            if topic:
                results = self.rag.search(topic, k=max(num_questions * 2, 5))
                contexts = [self._extract_text_from_result(r) for r in results]
            else:
                contexts = self.rag.reader_SQUAD(max_texts=num_questions * 4, sample_random=True)

            questions: List[str] = []
            used_contexts = set()
            
            for context in contexts:
                if len(questions) >= num_questions:
                    break
                
                snippet = context[:150]
                context_hash = hash(snippet)
                if context_hash in used_contexts:
                    continue
                used_contexts.add(context_hash)
                
                prompt_context = context.replace("\n", " ").strip()[:900]
                prompt = self.question_template.format(context=prompt_context)
                
                question = self._generate_with_gemini(prompt)
                if not question:
                    raise GeminiGenerationError("Gemini no devolvió una pregunta válida.")
                questions.append(question)
            
            return questions[:num_questions]
            
        except GeminiGenerationError:
            raise
        except Exception as e:
            print(f"Error generando preguntas (no relacionado con Gemini): {str(e)}")
    
    def _extract_text_from_result(self, result) -> str:
        if hasattr(result, "page_content"):
            return getattr(result, "page_content") or str(result)
        if isinstance(result, dict):
            return result.get("page_content") or result.get("content") or str(result)
        return str(result)
    
    
    def _generate_with_gemini(self, prompt: str) -> Optional[str]:
        """Generar usando google.generativeai con compatibilidad para versiones recientes del SDK."""
        try:
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise GeminiGenerationError("GEMINI_API_KEY no está configurada en las variables de entorno.")
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            
            text = response.text.strip() if hasattr(response, "text") else str(response)
            print(text)
            return text

        except Exception as e:
            print(f"Gemini failed with exception {e}")
            return None


    
    def _extract_keywords(self, text: str) -> List[str]:
        words = text.lower().split()
        stop_words = {'el', 'la', 'de', 'en', 'y', 'que', 'con', 'para', 'por', 'los', 'las', 'del', 'un', 'una'}
        keywords = [word.strip(".,:;()[]{}\"'") for word in words if word not in stop_words and len(word) > 3]
        seen = set()
        uniq = []
        for w in keywords:
            if w not in seen:
                seen.add(w)
                uniq.append(w)
            if len(uniq) >= 5:
                break
        return uniq
    
    def _clean_question(self, text: str) -> str:
        text = text.strip()
        if "." in text and "?" in text:
            qpos = text.find("?")
            if qpos != -1:
                text = text[: qpos + 1]
        if not text.endswith("?"):
            if "?" in text:
                text = text[: text.find("?") + 1]
            else:
                text = text.rstrip(".") + "?"
        text = text[0].upper() + text[1:] if text else text
        return text
