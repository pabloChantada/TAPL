import os
from typing import List, Optional
from .rag import RAG


class GeminiGenerationError(Exception):
    pass


class QuestionGenerator:
    def __init__(self, dataset_type: str = "squad"):
        """
        Inicializa el generador de preguntas con un tipo de dataset específico.

        Args:
            dataset_type: tipo de dataset ('squad', 'natural_questions', 'eli5', 'hotpotqa')
        """
        self.dataset_type = dataset_type
        self.rag = RAG(dataset_type=dataset_type)
        try:
            self.rag.load_chroma_db()
        except Exception as e:
            print(f"[QuestionGenerator] No se pudo cargar chroma DB en init: {e}")

        self.question_template = """
            Eres un experto examinador. Genera **UNA UNICA PREGUNTA** para evaluar a un usuario.
            Es un sistema de entrevistas, tu función es devolver **ÚNICAMENTE LA PREGUNTA** dado un contexto.
            La pregunta no debe superar los 100 caracteres y debe ser en **ESPAÑOL**. El contexto que vas a utilizar es: {context}
            """


    def set_dataset(self, dataset_type: str):
        """
        Cambia el dataset activo y recarga el RAG.

        Args:
            dataset_type: tipo de dataset ('squad', 'natural_questions', 'eli5', 'hotpotqa')
        """
        if dataset_type != self.dataset_type:
            self.dataset_type = dataset_type
            self.rag = RAG(dataset_type=dataset_type)
            try:
                self.rag.load_chroma_db()
                print(f"[QuestionGenerator] Dataset cambiado a: {dataset_type}")
            except Exception as e:
                print(
                    f"[QuestionGenerator] Error cargando nuevo dataset '{dataset_type}': {e}"
                )

    def generate_interview_questions(
        self, num_questions: int = 5, topic: str = ""
    ) -> List[str]:

        try:
            contexts = self.rag.read_dataset(
                max_texts=num_questions * 4, sample_random=True
            )

            questions = []
            used_contexts = set()

            for context in contexts:
                if len(questions) >= num_questions:
                    break

                snippet = context[:150]
                if snippet in used_contexts:
                    continue
                used_contexts.add(snippet)

                # 1. extraer la pregunta real del dataset
                raw_question = self._extract_dataset_question(context)

                # 2. normalizarla con gemini (limpiar latex + traducir)
                clean_question = self.normalize_question_with_gemini(raw_question)

                questions.append(clean_question)

            return questions[:num_questions]

        except Exception as e:
            print(f"Error generando preguntas: {str(e)}")


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
                raise GeminiGenerationError(
                    "GEMINI_API_KEY no está configurada en las variables de entorno."
                )

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            print("\n==============================")
            print("🧠 PROMPT ENVIADO A GEMINI:")
            print("==============================")
            print(prompt)
            print("==============================\n")
            response = model.generate_content(prompt)

            text = response.text.strip() if hasattr(response, "text") else str(response)
            print(text)
            return text

        except Exception as e:
            print(f"Gemini failed with exception {e}")
            return None

    def _extract_keywords(self, text: str) -> List[str]:
        words = text.lower().split()
        stop_words = {
            "el",
            "la",
            "de",
            "en",
            "y",
            "que",
            "con",
            "para",
            "por",
            "los",
            "las",
            "del",
            "un",
            "una",
        }
        keywords = [
            word.strip(".,:;()[]{}\"'")
            for word in words
            if word not in stop_words and len(word) > 3
        ]
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

    def _extract_dataset_question(self, text: str) -> str:
        """
        Extrae la pregunta desde el formato:
        'Pregunta: .... \nRespuesta: ...'
        """
        if "Pregunta:" in text:
            try:
                return text.split("Pregunta:")[1].split("Respuesta:")[0].strip()
            except:
                return text.strip()
        return text.strip()

    def normalize_question_with_gemini(self, raw_question: str) -> str:
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise GeminiGenerationError("GEMINI_API_KEY no está configurada.")

        genai.configure(api_key=api_key)

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

        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)

        return response.text.strip()

    def _extract_dataset_answer(self, text: str) -> str:
        """
        Extrae la respuesta correcta desde el formato:
        'Pregunta: ... \nRespuesta: ...'
        """
        if "Respuesta:" in text:
            try:
                return text.split("Respuesta:")[1].strip()
            except:
                return ""
        return ""
    def generate_single_question_with_answer(self):
        """
        Devuelve: (pregunta_limpia, respuesta_correcta)
        """
        contexts = self.rag.read_dataset(max_texts=10, sample_random=True)

        for ctx in contexts:
            raw_question = self._extract_dataset_question(ctx)
            correct_answer = self._extract_dataset_answer(ctx)

            clean_question = self.normalize_question_with_gemini(raw_question)

            return clean_question, correct_answer

        return None, None
