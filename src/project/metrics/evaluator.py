"""
Evaluador avanzado de respuestas abiertas para entrevistas cuantitativas.
Incluye:
- Similitud semántica SBERT
- Validación numérica
- Keyword Coverage
- Reasoning Structure Score
- Score híbrido final
- Placeholder para feedback basado en LLM
"""

import re
from typing import List, Dict
from sentence_transformers import SentenceTransformer, util

# ============================================================
# SBERT MODEL
# ============================================================

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


# ============================================================
# 1) SEMANTIC SIMILARITY
# ============================================================

def semantic_similarity(text_a: str, text_b: str) -> float:
    emb_a = embedding_model.encode(text_a, convert_to_tensor=True)
    emb_b = embedding_model.encode(text_b, convert_to_tensor=True)
    score = util.cos_sim(emb_a, emb_b)
    return float(score)


# ============================================================
# 2) NUMERIC VALIDATION
# ============================================================

def extract_number(text: str):
    nums = re.findall(r"\d+\.?\d*", text)
    return float(nums[-1]) if nums else None


def numeric_validation(correct_answer: str, user_answer: str, tol=1e-4) -> float:
    correct = extract_number(correct_answer)
    user = extract_number(user_answer)

    if correct is None or user is None:
        return 0.0
    if abs(correct - user) < tol:
        return 1.0
    return 0.0


# ============================================================
# 3) KEYWORD COVERAGE
# ============================================================

def extract_keywords(text: str, top_k: int = 6) -> List[str]:
    """
    Muy simple: palabras importantes por longitud (puedes reemplazarlo por spaCy)
    Devuelve una lista de palabras clave relevantes.
    """
    words = re.findall(r"[a-zA-Záéíóúñ]+", text.lower())
    words = [w for w in words if len(w) > 4]  # filtrar palabras inútiles
    words_sorted = sorted(words, key=len, reverse=True)
    return words_sorted[:top_k]


def keyword_coverage(correct_answer: str, user_answer: str) -> float:
    key_correct = set(extract_keywords(correct_answer))
    key_user = set(extract_keywords(user_answer))

    if not key_correct:
        return 0.0

    overlap = key_correct.intersection(key_user)
    return len(overlap) / len(key_correct)


# ============================================================
# 4) REASONING STRUCTURE SCORE
# ============================================================

def reasoning_structure_score(answer: str) -> float:
    """
    Evalúa si el usuario tiene estructura lógica.
    Reglas simples:
    - presencia de conectores lógicos: "por lo tanto", "entonces", "así que", "porque"
    - líneas separadas (pasos)
    - numeraciones (1., 2., etc.)

    Score entre 0 y 1.
    """
    score = 0
    answer_lower = answer.lower()

    connectors = ["por lo tanto", "entonces", "así que", "porque", "debido a", "consecuentemente"]
    steps_indicators = ["1.", "2.", "3.", "- ", "* "]

    # conectores lógicos
    if any(c in answer_lower for c in connectors):
        score += 0.4

    # líneas separadas
    if len(answer.split("\n")) > 1:
        score += 0.3

    # numeraciones
    if any(step in answer_lower for step in steps_indicators):
        score += 0.3

    return min(score, 1.0)


# ============================================================
# 5) HYBRID FINAL SCORE
# ============================================================

def final_hybrid_score(
    sem: float,
    num: float,
    keys: float,
    reasoning: float,
) -> float:
    """
    Peso profesional inspirado en sistemas educativos:
    """
    return (
        0.40 * sem +
        0.25 * num +
        0.20 * keys +
        0.15 * reasoning
    )


def evaluate_full(correct_answer: str, user_answer: str) -> Dict:
    sem = semantic_similarity(correct_answer, user_answer)
    num = numeric_validation(correct_answer, user_answer)
    keys = keyword_coverage(correct_answer, user_answer)
    reasoning = reasoning_structure_score(user_answer)

    final_score = final_hybrid_score(sem, num, keys, reasoning)

    return {
        "semantic_similarity": sem,
        "numeric_score": num,
        "keyword_coverage": keys,
        "reasoning_structure": reasoning,
        "final_score": final_score
    }
