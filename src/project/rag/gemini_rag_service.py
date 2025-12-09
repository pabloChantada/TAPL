import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiTheoryService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY no configurada")
        
        genai.configure(api_key=api_key)
        self.model_name = "gemini-2.5-flash-preview-09-2025"
        
        # Lee la variable "THEORY_BOOKS", separa por comas y limpia espacios
        books_env = os.getenv("THEORY_BOOKS", "")
        self.book_file_names = [b.strip() for b in books_env.split(",") if b.strip()]
        
        
        self.books = []
        self._load_books()

    def _load_books(self):
        """Recupera las referencias a los archivos ya subidos en Google."""
        try:
            for file_name in self.book_file_names:
                # genai.get_file recupera el puntero al archivo sin volver a subirlo
                file_ref = genai.get_file(file_name)
                self.books.append(file_ref)
                logger.info(f"📚 Libro cargado: {file_ref.display_name}")
        except Exception as e:
            logger.error(f"❌ Error cargando libros: {e}")
            # Es importante no fallar toda la app si un libro falla, 
            # pero sí avisar para revisarlo.

    def get_theory_explanation(self, question_text):
        if not self.books:
            return "No se han configurado los libros de teoría correctamente."

        model = genai.GenerativeModel(self.model_name)
        
        prompt = [
            f"""
            Actúa como un profesor experto en matemáticas y estadística.
            El estudiante tiene una duda sobre la siguiente pregunta de entrevista técnica:
            "{question_text}"
            
            Tu objetivo es explicar la TEORÍA matemática necesaria para entender este problema,
            utilizando ÚNICAMENTE la información contenida en los libros adjuntos.
            
            Instrucciones:
            1. Busca los conceptos clave en los libros proporcionados.
            2. Explica las fórmulas o teoremas relevantes.
            3. NO resuelvas el problema numéricamente, céntrate en el "por qué" y la teoría.
            4. Si es posible, cita el libro o capítulo de donde sacas la información.
            """,
            *self.books  # Pasamos los punteros a los archivos
        ]

        logger.info(f"Consultando teoría para: {question_text[:30]}...")
        
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generando explicación: {e}")
            return "Ocurrió un error consultando la biblioteca de teoría."