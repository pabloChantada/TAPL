"""
advanced_evaluator.py
Módulo de evaluación cuantitativa y lógica.
"""
import re
from typing import List, Dict, Any
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dependencias opcionales (para evitar errores si no están instaladas al inicio)
try:
    from sentence_transformers import SentenceTransformer, util
    import spacy
    from keybert import KeyBERT
    from sympy import sympify, simplify
except ImportError as e:
    logger.error(f"Faltan dependencias para el evaluador avanzado: {e}")
    logger.error("Ejecuta: pip install sentence-transformers spacy keybert sympy")
    raise

# ============================================================
# CARGA DE MODELOS (Lazy Loading para no bloquear inicio)
# ============================================================

class EvaluatorModels:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            logger.info("Cargando modelos de Evaluación Avanzada (esto puede tardar)...")
            cls._instance = super(EvaluatorModels, cls).__new__(cls)
            # Embedding Model
            cls._instance.embedding_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
            # NLP
            try:
                cls._instance.nlp = spacy.load("es_core_news_md")
            except OSError:
                logger.warning("Modelo 'es_core_news_md' no encontrado. Descargando...")
                from spacy.cli import download
                download("es_core_news_md")
                cls._instance.nlp = spacy.load("es_core_news_md")
            # KeyBERT
            cls._instance.kw_model = KeyBERT(model=cls._instance.embedding_model)
            logger.info("Modelos cargados correctamente.")
        return cls._instance

# ============================================================
# FUNCIONES DE EVALUACIÓN
# ============================================================

def semantic_similarity(text_a: str, text_b: str) -> float:
    models = EvaluatorModels()
    emb_a = models.embedding_model.encode(text_a, convert_to_tensor=True)
    emb_b = models.embedding_model.encode(text_b, convert_to_tensor=True)
    score = util.cos_sim(emb_a, emb_b)
    return float(score)

def extract_math_expr(text: str):
    # Intenta extraer expresiones matemáticas o números
    # Filtra texto para dejar solo chars matemáticos probables
    exprs = re.findall(r"[0-9\+\-\*\/\^\(\)Hh_e\.]+", text.replace(" ", ""))
    if exprs:
        # Devuelve la expresión más larga encontrada
        return max(exprs, key=len)
    return None

def numeric_validation(correct_answer: str, user_answer: str) -> float:
    correct = extract_math_expr(correct_answer)
    user = extract_math_expr(user_answer)

    if correct is None or user is None:
        return 0.0

    try:
        # Sympy validation
        c = simplify(sympify(correct))
        u = simplify(sympify(user))
        # Chequear equivalencia (resta es cero)
        return 1.0 if simplify(c - u) == 0 else 0.0
    except Exception:
        return 0.0

def extract_concepts(text: str) -> List[str]:
    models = EvaluatorModels()
    doc = models.nlp(text)
    noun_chunks = [chunk.text.lower() for chunk in doc.noun_chunks]
    # Extraer top 5 keywords
    keywords = [kw[0] for kw in models.kw_model.extract_keywords(text, top_n=5)]
    return list(set(noun_chunks + keywords))

def concept_coverage(correct_answer: str, user_answer: str) -> float:
    c1 = set(extract_concepts(correct_answer))
    c2 = set(extract_concepts(user_answer))
    if not c1: 
        return 0.0
    overlap = c1.intersection(c2)
    return len(overlap) / len(c1)

def reasoning_structure_score(answer: str) -> float:
    score = 0.0
    ans = answer.lower()
    
    # 1. Conectores Lógicos (Argumentación)
    logical_connectors = ["por lo tanto", "entonces", "así que", "porque", "debido a", "consecuentemente", "implica"]
    if any(c in ans for c in logical_connectors): score += 0.25

    # 2. Notación Matemática / Técnica
    math_indicators = ["e(", "σ", "sum", "∑", "1/", "recurrencia", "esperanza", "integral", "derivada", "^"]
    if any(m in ans for m in math_indicators): score += 0.25

    # 3. Estructura Secuencial (Pasos)
    step_indicators = ["1.", "2.", "primero", "luego", "finalmente", "paso"]
    if any(s in ans for s in step_indicators) or "\n" in answer: score += 0.25

    # 4. Definición de variables o casos
    def_indicators = ["sea", "definimos", "consideremos", "supongamos", "dado que"]
    if any(d in ans for d in def_indicators): score += 0.25

    return min(score, 1.0)

def final_hybrid_score(sem: float, num: float, concepts: float, reasoning: float) -> float:
    # Ponderación personalizada para problemas cuantitativos
    return (
        0.05 * sem +       # Similitud pura (menos peso en mates)
        0.30 * num +       # Exactitud numérica (Crucial)
        0.20 * concepts +  # Uso de terminología correcta
        0.45 * reasoning   # El proceso lógico es lo más importante
    )

def evaluate_full(correct_answer: str, user_answer: str) -> Dict[str, Any]:
    """
    Función principal a llamar desde el backend.
    """
    try:
        sem = semantic_similarity(correct_answer, user_answer)
        num = numeric_validation(correct_answer, user_answer)
        concepts = concept_coverage(correct_answer, user_answer)
        reasoning = reasoning_structure_score(user_answer)
        final = final_hybrid_score(sem, num, concepts, reasoning)

        return {
            "semantic_score": round(sem, 3),
            "numeric_score": round(num, 3),
            "concept_score": round(concepts, 3),
            "reasoning_score": round(reasoning, 3),
            "final_score": round(final, 3)
        }
    except Exception as e:
        logger.error(f"Error en evaluación: {e}")
        return {
            "semantic_score": 0, "numeric_score": 0, 
            "concept_score": 0, "reasoning_score": 0, 
            "final_score": 0, "error": str(e)
        }