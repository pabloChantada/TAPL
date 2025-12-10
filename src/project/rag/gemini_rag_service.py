import os
import logging

try:
    import google.generativeai as genai
except ImportError:
    pass

logger = logging.getLogger(__name__)

class GeminiTheoryService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "GEMINI").upper()
        self.api_key_gemini = os.getenv("GEMINI_API_KEY")
        
        self.books = []
        
        if self.provider in ["DEEPSEEK", "GROQ"]:
            logger.warning(f"THEORY SERVICE: RAG con archivos NO está soportado en {self.provider}.")
        else:
            if not self.api_key_gemini:
                logger.error("GEMINI_API_KEY no configurada. TheoryService no funcionará.")
                return

            genai.configure(api_key=self.api_key_gemini)
            self.model_name = "gemini-2.5-flash-preview-09-2025"
            
            books_env = os.getenv("THEORY_BOOKS", "")
            self.book_file_names = [b.strip() for b in books_env.split(",") if b.strip()]
            self._load_books()

    def _load_books(self):
        if self.provider != "GEMINI": 
            return
        try:
            for file_name in self.book_file_names:
                file_ref = genai.get_file(file_name)
                self.books.append(file_ref)
                logger.info(f"📚 Libro cargado: {file_ref.display_name}")
        except Exception as e:
            logger.error(f"Error cargando libros: {e}")

    def get_theory_explanation(self, question_text):
        if self.provider in ["DEEPSEEK", "GROQ"]:
            return (
                f"La consulta de teoría (RAG) no está disponible usando {self.provider}.\n"
                "Esta funcionalidad depende de Google Drive y solo funciona con Gemini."
            )

        if not self.books:
            return "No se han configurado los libros de teoría correctamente o no se pudieron cargar."

        model = genai.GenerativeModel(self.model_name)
        prompt = [
            f"""
            Actúa como un profesor experto en matemáticas.
            Explica la TEORÍA necesaria para entender: "{question_text}"
            Usa SOLO los libros adjuntos.
            """,
            *self.books
        ]
        
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generando explicación: {e}")
            return "Error consultando biblioteca."