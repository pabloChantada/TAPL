"""
Evaluador avanzado optimizado para preguntas cuantitativas y matemáticas.
Mejoras:
- Modelo SBERT más robusto
- Concept coverage en lugar de keyword length
- Validación matemática con SymPy
- Reasoning Score basado en estructura matemática
- Ponderación optimizada para reasoning
"""

import re
from typing import List, Dict
from sentence_transformers import SentenceTransformer, util
import spacy
from keybert import KeyBERT
from sympy import sympify, simplify

# ============================================================
# MODELOS
# ============================================================

# Mejor que MiniLM para razonamiento matemático
embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

# NLP para extracción de conceptos
nlp = spacy.load("es_core_news_md")

# Extracción semántica de keywords
kw_model = KeyBERT("sentence-transformers/all-mpnet-base-v2")


# ============================================================
# 1) SEMANTIC SIMILARITY
# ============================================================

def semantic_similarity(text_a: str, text_b: str) -> float:
    emb_a = embedding_model.encode(text_a, convert_to_tensor=True)
    emb_b = embedding_model.encode(text_b, convert_to_tensor=True)
    score = util.cos_sim(emb_a, emb_b)
    return float(score)


# ============================================================
# 2) NUMERIC + MATH VALIDATION (SymPy)
# ============================================================

def extract_math_expr(text: str):
    """
    Intenta extraer una expresión matemática o un número.
    """
    expr = re.findall(r"[0-9\+\-\*\/\^\(\)Hh_]+", text.replace(" ", ""))
    if expr:
        return expr[-1]  # última expresión relevante
    return None


def numeric_validation(correct_answer: str, user_answer: str) -> float:
    """
    Usa sympy para validar expresiones equivalentes.
    Ej: 52*H51 == 52*(1 + 1/2 + ... + 1/51)
    """
    correct = extract_math_expr(correct_answer)
    user = extract_math_expr(user_answer)

    if correct is None or user is None:
        return 0.0

    try:
        c = simplify(sympify(correct))
        u = simplify(sympify(user))
        return 1.0 if simplify(c - u) == 0 else 0.0
    except:
        return 0.0


# ============================================================
# 3) CONCEPT COVERAGE (mejor que keyword coverage)
# ============================================================

def extract_concepts(text: str) -> List[str]:
    """
    Extrae conceptos matemáticos relevantes usando spaCy + KeyBERT.
    """
    doc = nlp(text)

    # chunks nominales como "posición de la carta", "relación de recurrencia"
    noun_chunks = [chunk.text.lower() for chunk in doc.noun_chunks]

    # keywords semánticas
    keywords = [kw[0] for kw in kw_model.extract_keywords(text, top_n=5)]

    concepts = noun_chunks + keywords
    return list(set(concepts))


def concept_coverage(correct_answer: str, user_answer: str) -> float:
    c1 = set(extract_concepts(correct_answer))
    c2 = set(extract_concepts(user_answer))

    if not c1:
        return 0.0

    overlap = c1.intersection(c2)
    return len(overlap) / len(c1)


# ============================================================
# 4) MATHEMATICAL REASONING SCORE
# ============================================================

def reasoning_structure_score(answer: str) -> float:
    """
    Analiza estructura matemática:
    - pasos numerados
    - notación matemática: E(i), Σ, 1/52
    - conectores lógicos
    - presencia de definiciones
    """

    score = 0.0
    ans = answer.lower()

    logical_connectors = [
        "por lo tanto", "entonces", "así que", "porque",
        "debido a", "consecuentemente", "en consecuencia"
    ]

    math_indicators = [
        "e(", "σ", "sum", "∑", "1/", "recurrencia",
        "esperanza", "valor esperado"
    ]

    step_indicators = ["1.", "2.", "3.", "primero", "luego", "finalmente"]

    # Conectores lógicos
    if any(c in ans for c in logical_connectors):
        score += 0.25

    # Notación matemática
    if any(m in ans for m in math_indicators):
        score += 0.25

    # Estructura paso a paso
    if any(s in ans for s in step_indicators) or "\n" in answer:
        score += 0.25

    # Divide el problema en casos o define variables
    if "sea" in ans or "definimos" in ans or "consideremos" in ans:
        score += 0.25

    return min(score, 1.0)


# ============================================================
# 5) HYBRID FINAL SCORE (optimizado para matemáticas)
# ============================================================

def final_hybrid_score(
    sem: float,
    num: float,
    concepts: float,
    reasoning: float,
) -> float:
    """
    Matemáticas → razonamiento y exactitud pesan más.
    """
    return (
        0.05 * sem +       # mínima importancia
        0.25 * num +       # exactitud numérica es importante
        0.15 * concepts +  # cobertura conceptual
        0.55 * reasoning   # razonamiento es el núcleo
    )


# ============================================================
# 7) EVALUADOR COMPLETO
# ============================================================

def evaluate_full(correct_answer: str, user_answer: str) -> Dict:
    sem = semantic_similarity(correct_answer, user_answer)
    num = numeric_validation(correct_answer, user_answer)
    concepts = concept_coverage(correct_answer, user_answer)
    reasoning = reasoning_structure_score(user_answer)

    final_score = final_hybrid_score(sem, num, concepts, reasoning)

    return {
        "semantic_similarity": sem,
        "numeric_score": num,
        "concept_coverage": concepts,
        "reasoning_structure": reasoning,
        "final_score": final_score
    }
