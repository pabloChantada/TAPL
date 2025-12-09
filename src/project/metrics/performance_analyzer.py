import os
import google.generativeai as genai


class PerformanceAnalyzer:
    def __init__(self):
        api_key = os. getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2. 5-flash")

    def generate_performance_summary(
        self, 
        answers: list, 
        global_score: dict,
        dataset_type: str
    ) -> str:
        """
        Genera un resumen textual del desempeño del usuario. 
        """
        # Preparar contexto para el LLM
        answers_text = "\n".join([
            f"P{a['question_number']}: {a['question']}\n"
            f"  Usuario: {a['answer']}\n"
            f"  Correcta: {a. get('correct_answer', 'N/A')}\n"
            f"  Score parcial: {a. get('metrics', {}).get('score_parcial', 'N/A')}"
            for a in answers
        ])
        
        print(f"[DEBUG] Contexto para LLM:\n{answers_text}")
        
        prompt = f"""
        Eres un evaluador experto en entrevistas técnicas. 
        
        Analiza el siguiente desempeño de un candidato:
        
        **Dataset evaluado:** {dataset_type}
        **Score Global:** {global_score['score']}/100 ({global_score['nivel']})
        
        **Respuestas:**
        {answers_text}
        
        Genera un resumen ejecutivo de 3-4 párrafos que incluya:
        1. Evaluación general del desempeño
        2. Fortalezas identificadas
        3.  Áreas de mejora específicas
        4.  Recomendaciones concretas para el candidato
        
        Sé constructivo y profesional.  Responde en español.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response. text. strip()
        except Exception as e:
            print(f"Error generando resumen: {e}")
            return f"Score: {global_score['score']}/100.  {global_score['descripcion']}"
