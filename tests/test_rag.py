
import json
import os
import random
import pytest

import importlib
rag_module = importlib.import_module("src.project.rag.rag")  # ahora rag_module es el módulo rag.py
from src.project.rag import RAG


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def make_squad_json(n_qas):
    # Construye un JSON tipo SQuAD con n_qas preguntas en un solo paragraph
    qas = []
    for i in range(n_qas):
        qas.append({"question": f"question_{i}", "answers": [{"text": f"answer_{i}"}], "id": str(i)})
    data = {
        "data": [
            {
                "title": "test",
                "paragraphs": [
                    {
                        "context": "This is the context.",
                        "qas": qas,
                    }
                ],
            }
        ]
    }
    return data


def test_reader_squad_respects_max_texts_and_sample(tmp_path):
    # Crear varios archivos JSON en tmp_path
    file1 = tmp_path / "db1.json"
    file2 = tmp_path / "db2.json"

    # db1 tiene 3 pares, db2 tiene 4 pares -> total 7
    write_json(file1, make_squad_json(3))
    write_json(file2, make_squad_json(4))

    rag = RAG(db_path=str(tmp_path), verbose=False)

    # Sin límite: debería devolver 7
    all_texts = rag.reader_SQUAD()
    assert len(all_texts) == 7

    # Limitar a 2 (sin sample aleatorio) -> primeros 2
    first_two = rag.reader_SQUAD(max_texts=2, sample_random=False)
    assert len(first_two) == 2

    # Limitar a 3 con sample aleatorio -> longitud 3 (contenido puede variar)
    random.seed(0)
    sampled = rag.reader_SQUAD(max_texts=3, sample_random=True)
    assert len(sampled) == 3
    # Formato esperado
    for t in sampled:
        assert "Contexto:" in t and "Pregunta:" in t and "Respuesta:" in t


def test_chunker_respects_max_chunks(monkeypatch):
    # Mock del RecursiveCharacterTextSplitter para devolver chunks predecibles
    class DummySplitter:
        def __init__(self, chunk_size=None, chunk_overlap=None, length_function=None, add_start_index=None):
            pass

        def split_text(self, text):
            # Devuelve 10 chunks por cada texto
            return [f"chunk_{i}" for i in range(10)]

    monkeypatch.setattr(rag_module, "RecursiveCharacterTextSplitter", DummySplitter)

    rag = RAG(db_path=".", verbose=False)
    # Dos textos -> cada uno genera 10 chunks, pero max_chunks=5 debe truncar a 5
    chunks = rag.chunker(["texto1", "texto2"], chunk_size=10, max_chunks=5)
    assert len(chunks) == 5
    assert chunks == ["chunk_0", "chunk_1", "chunk_2", "chunk_3", "chunk_4"]


def test_create_chroma_db_calls_from_texts_and_persists(monkeypatch, tmp_path):
    # Mockear reader_SQUAD para devolver un número controlado de textos
    monkeypatch.setattr(RAG, "reader_SQUAD", lambda self, max_texts=None, sample_random=False: ["t1", "t2"])

    # Mockear chunker para devolver chunks conocidas
    monkeypatch.setattr(RAG, "chunker", lambda self, qa_texts, chunk_size=1024, max_chunks=None: ["c1", "c2", "c3"])

    # Mockear _get_embeddings para devolver un objeto marcador
    mock_embedding = object()
    monkeypatch.setattr(RAG, "_get_embeddings", lambda self: mock_embedding)

    # Mock Chroma con from_texts que registra la llamada
    class MockChroma:
        last_call = None
        init_args = None

        def __init__(self, persist_directory=None, embedding_function=None):
            MockChroma.init_args = {"persist_directory": persist_directory, "embedding_function": embedding_function}

        @classmethod
        def from_texts(cls, texts, embedding, persist_directory):
            cls.last_call = {"texts": texts, "embedding": embedding, "persist_directory": persist_directory}
            return cls(persist_directory=persist_directory, embedding_function=embedding)

    monkeypatch.setattr(rag_module, "Chroma", MockChroma)

    # Usar tmp_path como db_path para verificar ruta de persistencia
    rag = RAG(db_path=str(tmp_path), verbose=False)
    rag.create_chroma_db(sample_size=1, sample_random=False, chunk_size=512, max_chunks=None, verbose=False)

    # Comprobar que from_texts fue llamado con los chunks devueltos por chunker
    assert MockChroma.last_call is not None
    assert MockChroma.last_call["texts"] == ["c1", "c2", "c3"]
    assert MockChroma.last_call["embedding"] is mock_embedding
    expected_persist = os.path.join(str(tmp_path), "chroma_db")
    assert MockChroma.last_call["persist_directory"] == expected_persist

    # Comprobar que la instancia también recibió los mismos argumentos al construir
    assert MockChroma.init_args["persist_directory"] == expected_persist
    assert MockChroma.init_args["embedding_function"] is mock_embedding


def test_load_chroma_db_uses_embedding_function(monkeypatch, tmp_path):
    # Mock _get_embeddings para devolver objeto
    mock_embedding = object()
    monkeypatch.setattr(RAG, "_get_embeddings", lambda self: mock_embedding)

    # Mock Chroma para capturar init args
    class MockChroma2:
        init_args = None

        def __init__(self, persist_directory=None, embedding_function=None):
            MockChroma2.init_args = {"persist_directory": persist_directory, "embedding_function": embedding_function}

    monkeypatch.setattr(rag_module, "Chroma", MockChroma2)

    rag = RAG(db_path=str(tmp_path), verbose=False)
    rag.load_chroma_db(verbose=False)

    expected_persist = os.path.join(str(tmp_path), "chroma_db")
    assert MockChroma2.init_args is not None
    assert MockChroma2.init_args["persist_directory"] == expected_persist
    assert MockChroma2.init_args["embedding_function"] is mock_embedding
