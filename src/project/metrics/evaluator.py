"""
advanced_evaluator.py
Módulo de evaluación cuantitativa y lógica.
"""
import re
from typing import List, Dict, Any, Iterable
import logging
from difflib import SequenceMatcher
from unidecode import unidecode

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
    logger.error("Ejecuta: pip install sentence-transformers spacy keybert sympy unidecode")
    raise

# Stopwords simples en español para limpieza de conceptos
STOPWORDS_ES = {
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "al", "a", "en", "y", "o", "u", "que", "con",
    "por", "para", "como", "es", "son", "sea", "ser", "se",
    "lo", "su", "sus", "suya", "suyo", "suya", "este", "esta",
    "esto", "ese", "esa", "eso", "hay", "si", "sí",
    "no", "dado", "dada", "dadas", "dados"
}

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
# HELPERS
# ============================================================

def _normalize_token(tok: str) -> str:
    tok = unidecode(tok.lower().strip())
    tok = re.sub(r"[^\w\-/\.]", " ", tok)
    tok = tok.strip()
    return tok

def _fuzzy_match(a: str, b: str, threshold: float = 0.85) -> bool:
    if not a or not b:
        return False
    if a == b:
        return True
    # Coincidencia por contención para términos cortos
    if len(a) >= 3 and len(b) >= 3 and (a in b or b in a):
        return True
    return SequenceMatcher(None, a, b).ratio() >= threshold

def _tokenize_basic(text: str) -> List[str]:
    text = unidecode(text.lower())
    parts = re.split(r"[^a-z0-9\-/\.]+", text)
    return [p for p in parts if p and len(p) > 1 and p not in STOPWORDS_ES]

def _extract_numbers(text: str) -> List[float]:
    normalized = text.replace(",", ".")
    nums = re.findall(r"-?\d+(?:\.\d+)?", normalized)
    return [float(n) for n in nums]

def _extract_fractions(text: str) -> List[float]:
    normalized = text.replace(",", ".")
    fracs = []
    for num, den in re.findall(r"(-?\d+(?:\.\d+)?)\s*/\s*(-?\d+(?:\.\d+)?)", normalized):
        try:
            d = float(den)
            if d == 0:
                continue
            fracs.append(float(num) / d)
        except Exception:
            continue
    return fracs

# ============================================================
# FUNCIONES DE EVALUACIÓN
# ============================================================

def semantic_similarity(text_a: str, text_b: str) -> float:
    models = EvaluatorModels()
    emb_a = models.embedding_model.encode(text_a, convert_to_tensor=True)
    emb_b = models.embedding_model.encode(text_b, convert_to_tensor=True)
    score = util.cos_sim(emb_a, emb_b)
    scaled = (float(score) + 1) / 2  # [-1,1] -> [0,1]
    return max(0.0, min(1.0, scaled))

def extract_math_expr(text: str):
    """
    Intenta extraer una expresión matemática sencilla.
    - Prioriza patrones tipo 'N = valor'.
    - Si no encuentra, devuelve None (se usará el plan B con números sueltos).
    """
    normalized = text.replace(",", ".")
    match = re.search(r"[Nn]\s*=\s*(-?\d+(?:\.\d+)?)", normalized)
    if match:
        return match.group(1)

    exprs = re.findall(r"[0-9\+\-\*\/\^\(\)\.\s]+", normalized)
    exprs = [e.strip() for e in exprs if e.strip()]
    if exprs:
        return max(exprs, key=len)
    return None

def numeric_validation(correct_answer: str, user_answer: str) -> float:
    """
    Estrategia híbrida:
    1) Intenta equivalencia exacta con sympy (si hay expresiones).
    2) Si falla, compara el número/razón más representativo con tolerancia adaptable.
    """
    correct_expr = extract_math_expr(correct_answer)
    user_expr = extract_math_expr(user_answer)

    if correct_expr and user_expr:
        try:
            c = simplify(sympify(correct_expr))
            u = simplify(sympify(user_expr))
            if simplify(c - u) == 0:
                return 1.0
        except Exception:
            pass  # Seguimos al plan B

    def candidates(text: str) -> List[float]:
        cands = []
        seen = set()
        for val in _extract_fractions(text) + _extract_numbers(text):
            key = round(val, 8)
            if key not in seen:
                seen.add(key)
                cands.append(val)
        return cands

    c_cands = candidates(correct_answer)
    u_cands = candidates(user_answer)

    if not c_cands or not u_cands:
        return 0.0

    best_rel = 1e9
    for c in c_cands:
        for u in u_cands:
            rel = abs(c - u) / max(abs(c), abs(u), 1)
            best_rel = min(best_rel, rel)

    if best_rel <= 0.02:
        return 1.0
    if best_rel <= 0.10:
        return max(0.5, 1.0 - (best_rel - 0.02) / 0.08 * 0.5)
    if best_rel <= 0.25:
        return max(0.2, 0.5 - (best_rel - 0.10) / 0.15 * 0.3)
    return 0.0

def extract_concepts(text: str) -> List[str]:
    """
    Extrae conceptos combinando:
    - chunks nominales lematizados (spaCy)
    - sustantivos y nombres propios individuales (más laxo)
    - keywords (KeyBERT)
    - tokens básicos limpiados (fallback)
    """
    models = EvaluatorModels()
    doc = models.nlp(text)

    noun_chunks = [_normalize_token(chunk.lemma_) for chunk in doc.noun_chunks]
    noun_chunks = [t for t in noun_chunks if t and len(t) > 1 and t not in STOPWORDS_ES]

    nouns = [
        _normalize_token(tok.lemma_)
        for tok in doc
        if tok.pos_ in {"NOUN", "PROPN"} and len(tok) > 1
    ]
    nouns = [t for t in nouns if t and len(t) > 1 and t not in STOPWORDS_ES]

    keywords = [kw[0] for kw in models.kw_model.extract_keywords(text, top_n=7)]
    keywords = [_normalize_token(k) for k in keywords if k]

    basic_tokens = _tokenize_basic(text)

    combined = set([t for t in noun_chunks + nouns + keywords + basic_tokens if t])
    return list(combined)

def _fuzzy_overlap(c1: Iterable[str], c2: Iterable[str], threshold: float = 0.75) -> int:
    overlap = 0
    c2_list = list(c2)
    for a in c1:
        if any(_fuzzy_match(a, b, threshold) for b in c2_list):
            overlap += 1
    return overlap

def concept_coverage(correct_answer: str, user_answer: str) -> float:
    c1 = set(extract_concepts(correct_answer))
    c2 = set(extract_concepts(user_answer))
    if not c1:
        return 0.0

    exact_overlap = len(c1.intersection(c2))
    fuzzy_overlap = _fuzzy_overlap(c1, c2, threshold=0.75)
    overlap = max(exact_overlap, fuzzy_overlap)

    coverage = overlap / len(c1)
    # Más laxo: pequeño “piso” si hay alguna coincidencia difusa
    if coverage == 0 and fuzzy_overlap > 0:
        coverage = min(0.2, fuzzy_overlap / len(c1) + 0.05)
    return max(0.0, min(1.0, coverage))

def reasoning_structure_score(answer: str) -> float:
    score = 0.0
    ans = answer.lower()
    
    logical_connectors = ["por lo tanto", "entonces", "así que", "porque", "debido a", "consecuentemente", "implica"]
    if any(c in ans for c in logical_connectors): score += 0.25

    math_indicators = ["e(", "σ", "sum", "∑", "1/", "recurrencia", "esperanza", "integral", "derivada", "^"]
    if any(m in ans for m in math_indicators): score += 0.25

    step_indicators = ["1.", "2.", "primero", "luego", "finalmente", "paso"]
    if any(s in ans for s in step_indicators) or "\n" in answer: score += 0.25

    def_indicators = ["sea", "definimos", "consideremos", "supongamos", "dado que"]
    if any(d in ans for d in def_indicators): score += 0.25

    return min(score, 1.0)

def final_hybrid_score(sem: float, num: float, concepts: float, reasoning: float) -> float:
    """
    Ponderación:
    - Similitud semántica (15%)
    - Precisión numérica (60%)
    - Cobertura conceptual / terminología (10%)
    - Razonamiento estructurado (15%)
    """
    score = (
        0.15 * sem +
        0.60 * num +
        0.10 * concepts +
        0.15 * reasoning
    )
    return max(0.0, min(1.0, score))

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