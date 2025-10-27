import evaluate


class Metrics:
    def __init__(self) -> None:
        # Carga de métricas
        self._bleu_metric = evaluate.load("bleu")
        self._rouge_metric = evaluate.load("rouge")
        self._bertscore_metric = evaluate.load("bertscore")

    def bleu(self, predictions, references):
        """Devuelve la puntuación BLEU promedio"""
        result = self._bleu_metric.compute(
            predictions=predictions, references=references
        )
        print(f"BLEU: {result}")
        return result["bleu"]

    def rouge(self, predictions, references):
        """Devuelve las métricas ROUGE"""
        result = self._rouge_metric.compute(
            predictions=predictions, references=references
        )
        print(f"ROUGE: {result}")
        return result

    def bertscore(self, predictions, references, lang="es"):
        """Devuelve la media de F1 en BERTScore"""
        result = self._bertscore_metric.compute(
            predictions=predictions, references=references, lang=lang
        )
        print(f"BERTSCORE: {result}")
        return sum(result["f1"]) / len(result["f1"])
