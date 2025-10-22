# Exponer la clase RAG definida en rag.py cuando se importe el package src.project.rag
from .rag import RAG

__all__ = ["RAG"]
