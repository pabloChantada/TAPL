import evaluate


class Metrics:
    def __init__(self) -> None:
        # Carga de métricas
        self._bleu_metric = evaluate.load("bleu")
        self._rouge_metric = evaluate.load("rouge")
        self._bertscore_metric = evaluate. load("bertscore")
        
        # Pesos para el score global
        self. weights = {
            "bleu": 0.20,
            "rouge_l": 0.25,
            "bertscore": 0.55  # Mayor peso a similitud semántica
        }

    def bleu(self, predictions, references):
        """Devuelve la puntuación BLEU promedio"""
        result = self._bleu_metric.compute(
            predictions=predictions, references=references
        )
        print(f"BLEU: {result}")
        return result["bleu"]

    def rouge(self, predictions, references):
        """Devuelve las métricas ROUGE"""
        result = self._rouge_metric. compute(
            predictions=predictions, references=references
        )
        print(f"ROUGE: {result}")
        return result

    def bertscore(self, predictions, references, lang="es"):
        """Devuelve la media de F1 en BERTScore"""
        print(f"[Metrics] Calculando BERTScore para {len(predictions)} predicciones...")
        try:
            metric = self._bertscore_metric
            result = metric.compute(
                predictions=predictions, 
                references=references, 
                lang=lang,
                device="cpu",  # Forzar CPU para evitar problemas
                batch_size=1   # Procesar de uno en uno
            )
            score = sum(result["f1"]) / len(result["f1"])
            print(f"[Metrics] BERTScore F1: {score}")
            return score
        except Exception as e:
            print(f"[Metrics] Error en BERTScore: {e}")
            return 0.0

    def global_score(self, bleu_score: float, rouge_scores: dict, bertscore: float) -> dict:
        """
        Calcula un score global ponderado de 0-100 y determina el nivel de desempeño. 
        
        Returns:
            dict con score, nivel y descripción
        """
        rouge_l = rouge_scores.get("rougeL", 0)
        
        # Score ponderado (0-1)
        weighted_score = (
            self.weights["bleu"] * bleu_score +
            self.weights["rouge_l"] * rouge_l +
            self.weights["bertscore"] * bertscore
        )
        
        # Convertir a escala 0-100
        score_100 = round(weighted_score * 100, 1)
        
        # Determinar nivel
        if score_100 >= 85:
            nivel = "Excelente"
            descripcion = "Dominio excepcional del tema.  Respuestas precisas y completas."
            color = "green"
        elif score_100 >= 70:
            nivel = "Bueno"
            descripcion = "Buen entendimiento general con algunas áreas de mejora."
            color = "blue"
        elif score_100 >= 50:
            nivel = "Aceptable"
            descripcion = "Conocimientos básicos demostrados.  Recomendable profundizar."
            color = "yellow"
        else:
            nivel = "Necesita Mejora"
            descripcion = "Se recomienda revisar los conceptos fundamentales."
            color = "red"
        
        return {
            "score": score_100,
            "nivel": nivel,
            "descripcion": descripcion,
            "color": color,
            "desglose": {
                "bleu_contrib": round(self.weights["bleu"] * bleu_score * 100, 1),
                "rouge_contrib": round(self. weights["rouge_l"] * rouge_l * 100, 1),
                "bertscore_contrib": round(self. weights["bertscore"] * bertscore * 100, 1)
            }
        }

    def classify_question_difficulty(self, correct_answer: str) -> dict:
        """
        Clasifica la dificultad de una pregunta basándose en la respuesta correcta.
        
        Returns:
            dict con nivel de dificultad y justificación
        """
        answer_length = len(correct_answer. split())
        
        # Detectar complejidad matemática
        math_indicators = ["²", "³", "√", "π", "∑", "∫", "∞", "≠", "≤", "≥", "×", "÷"]
        has_math = any(ind in correct_answer for ind in math_indicators)
        
        # Detectar términos técnicos (heurística simple)
        technical_words = len([w for w in correct_answer.split() if len(w) > 10])
        
        # Calcular dificultad
        difficulty_score = 0
        difficulty_score += min(answer_length / 50, 1) * 30  # Longitud (max 30 pts)
        difficulty_score += (30 if has_math else 0)  # Matemáticas
        difficulty_score += min(technical_words * 10, 40)  # Vocabulario técnico
        
        if difficulty_score >= 60:
            return {"nivel": "Difícil", "color": "red", "score": round(difficulty_score)}
        elif difficulty_score >= 30:
            return {"nivel": "Media", "color": "yellow", "score": round(difficulty_score)}
        else:
            return {"nivel": "Fácil", "color": "green", "score": round(difficulty_score)}

    def evaluate_single_answer(self, prediction: str, reference: str, lang: str = "es") -> dict:
        """
        Evalúa una respuesta individual con todas las métricas. 
        """
        bleu = self._bleu_metric. compute(predictions=[prediction], references=[[reference]])["bleu"]
        rouge = self._rouge_metric.compute(predictions=[prediction], references=[reference])
        bert = self._bertscore_metric.compute(predictions=[prediction], references=[reference], lang=lang)
        bertscore_f1 = bert["f1"][0]
        
        return {
            "bleu": round(bleu, 4),
            "rouge_l": round(rouge["rougeL"], 4),
            "bertscore_f1": round(bertscore_f1, 4),
            "score_parcial": round(
                (self.weights["bleu"] * bleu + 
                 self. weights["rouge_l"] * rouge["rougeL"] + 
                 self.weights["bertscore"] * bertscore_f1) * 100, 1
            )
        }