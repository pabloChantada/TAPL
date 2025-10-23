
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import torch

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_DIR = os.path.join(BASE_DIR, "database")


class RAG:
    def __init__(
        self,
        db_path: str = DB_DIR,
        model_embedder: str = "sentence-transformers/multi-qa-mpnet-base-dot-v1",
        verbose: bool = False,
    ):
        """
        RAG helper.

        Args:
            db_path: ruta base donde se guardará chroma_db.
            model_embedder: modelo de embeddings.
            verbose: si True imprime información extra durante las operaciones.
        """
        self.db_path = db_path
        self.model_embedder = model_embedder
        self.db = None
        self.verbose = verbose

        if torch.cuda.is_available():
            self.device = "cuda"
            self.batch_size = 64
            if self.verbose:
                print(f"[RAG] GPU detectada: {torch.cuda.get_device_name(0)}")
        elif torch.backends.mps.is_available():
            self.device = "mps"
            self.batch_size = 32
            if self.verbose:
                print("[RAG] GPU detectada usando MPS")
        else:
            self.device = "cpu"
            self.batch_size = 8
            if self.verbose:
                print("[RAG] Usando CPU")

    def _get_embeddings(self):
        """Crear instancia de embeddings (usa self.batch_size y self.device)."""
        if self.verbose:
            print(f"[RAG] Creando embeddings con modelo {self.model_embedder} en {self.device} (batch_size={self.batch_size})")
        return HuggingFaceEmbeddings(
            model_name=self.model_embedder,
            model_kwargs={
                "device": self.device,
                "trust_remote_code": True,
            },
            encode_kwargs={
                "normalize_embeddings": True,
                "batch_size": self.batch_size,
            },
        )

    def reader_SQUAD(self, max_texts: int | None = None, sample_random: bool = False):
        """
        Leer todos los archivos JSON en la carpeta database y extraer pares QA en formato SQuAD.

        Args:
            max_texts: si se pasa un entero, limita la salida a los primeros N pares (o N aleatorios si sample_random=True).
            sample_random: si True y max_texts definido, selecciona una muestra aleatoria de qa_texts.
        Returns:
            Lista de strings con "Contexto: ... \nPregunta: ... \nRespuesta: ..."
        """
        qa_texts = []

        files = [f for f in os.listdir(self.db_path) if f.endswith(".json")]
        if self.verbose:
            print(f"[RAG] Buscando archivos .json en {self.db_path} → {len(files)} encontrados")

        for i, file in enumerate(files, start=1):
            path = os.path.join(self.db_path, file)
            try:
                df = pd.read_json(path)
            except Exception as e:
                if self.verbose:
                    print(f"[RAG] No se pudo leer {path}: {e}")
                continue

            # Formato SQuAD esperado: df['data']
            for data_row in df.get("data", []):
                for paragraph in data_row.get("paragraphs", []):
                    context = paragraph.get("context", "")
                    for qa in paragraph.get("qas", []):
                        question = qa.get("question", "")
                        answers = qa.get("answers", [])
                        answer = answers[0].get("text", "") if answers else ""
                        if context and question and answer:
                            text_block = f"Contexto: {context}\nPregunta: {question}\nRespuesta: {answer}"
                            qa_texts.append(text_block)

            if self.verbose and i % 5 == 0:
                print(f"[RAG] Procesados {i}/{len(files)} archivos")

        total = len(qa_texts)
        if self.verbose:
            print(f"[RAG] Pares QA construidos totales: {total}")

        if max_texts is not None and total > max_texts:
            if sample_random:
                if self.verbose:
                    print(f"[RAG] Muestreando aleatoriamente {max_texts} pares para testing")
                indices = np.random.choice(total, size=max_texts, replace=False)
                qa_texts = [qa_texts[i] for i in indices]
            else:
                if self.verbose:
                    print(f"[RAG] Limitando a los primeros {max_texts} pares para testing")
                qa_texts = qa_texts[:max_texts]

        if self.verbose:
            print(f"[RAG] Pares QA devueltos: {len(qa_texts)}")
        return qa_texts

    def chunker(self, qa_texts, chunk_size: int = 1024, max_chunks: int | None = None):
        """
        Dividir pares QA en chunks más pequeños.

        Args:
            qa_texts: lista de textos a dividir.
            chunk_size: tamaño máximo de cada chunk.
            max_chunks: si se pasa, limita el número total de chunks devueltos.
        Returns:
            Lista de chunks (strings).
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=128,
            length_function=len,
            add_start_index=True,
        )

        all_chunks = []
        for i, text in enumerate(qa_texts, start=1):
            chunks = splitter.split_text(text)
            all_chunks.extend(chunks)
            if self.verbose and i % 50 == 0:
                print(f"[RAG] Chunking: procesados {i}/{len(qa_texts)} textos -> {len(all_chunks)} chunks")

            # Si ya alcanzamos el límite de chunks, interrumpimos
            if max_chunks is not None and len(all_chunks) >= max_chunks:
                if self.verbose:
                    print(f"[RAG] Alcanzado max_chunks={max_chunks}, deteniendo chunker")
                all_chunks = all_chunks[:max_chunks]
                break

        if self.verbose:
            print(f"[RAG] Total de chunks creados: {len(all_chunks)}")
        return all_chunks

    def create_chroma_db(
        self,
        sample_size: int | None = None,
        sample_random: bool = False,
        chunk_size: int = 1024,
        max_chunks: int | None = None,
        verbose: bool | None = None,
    ):
        """
        Crea y guarda una base vectorial con Chroma.

        Args:
            sample_size: si se pasa un entero, solo se usan hasta sample_size pares QA (útil para testing).
            sample_random: si True y sample_size definido, la selección será aleatoria.
            chunk_size: tamaño de chunk para splitter.
            max_chunks: si se pasa, limita el número total de chunks a indexar (útil para testing).
            verbose: override del verbosity por llamada.
        """
        if verbose is None:
            verbose = self.verbose

        if verbose:
            print(f"[RAG] Iniciando creación de la DB (sample_size={sample_size}, sample_random={sample_random}, chunk_size={chunk_size}, max_chunks={max_chunks})")

        qa_texts = self.reader_SQUAD(max_texts=sample_size, sample_random=sample_random)
        if not qa_texts:
            raise ValueError("No text to generate the embedding database")

        chunks = self.chunker(qa_texts, chunk_size=chunk_size, max_chunks=max_chunks)
        if not chunks:
            raise ValueError("No chunks created from the texts")

        embeddings = self._get_embeddings()

        if verbose:
            print(f"[RAG] Creando Database con {len(chunks)} chunks en {os.path.join(self.db_path, 'chroma_db')}")

        self.db = Chroma.from_texts(
            texts=chunks,
            embedding=embeddings,
            persist_directory=os.path.join(self.db_path, "chroma_db"),
        )

        if verbose:
            print("[RAG] Base de datos creada y persistida")

    def load_chroma_db(self, verbose: bool | None = None):
        """Cargar base de datos existente"""
        if verbose is None:
            verbose = self.verbose
        embeddings = self._get_embeddings()
        if verbose:
            print(f"[RAG] Cargando DB desde {os.path.join(self.db_path, 'chroma_db')}")
        self.db = Chroma(
            persist_directory=os.path.join(self.db_path, "chroma_db"),
            embedding_function=embeddings,
        )
        if verbose:
            print("[RAG] DB cargada")

    def search(self, query: str, k: int = 5, verbose: bool | None = None):
        """Buscar contextos similares a una query"""
        if verbose is None:
            verbose = self.verbose
        if not self.db:
            if verbose:
                print("[RAG] DB no cargada, intentando load_chroma_db()")
            self.load_chroma_db(verbose=verbose)
        results = self.db.similarity_search(query, k=k)
        if verbose:
            print(f"[RAG] Se encontraron {len(results)} contextos similares.")
        return results
    


if __name__ == "__main__":
    # Ejemplos de uso para testing reducido:
    rag = RAG(verbose=True)
    # Para testing rápido: solo indexar 10 pares QA (aleatorios), y limitar a 50 chunks totales
    rag.create_chroma_db(sample_random=True, chunk_size=512, max_chunks=50, verbose=True)
    print("Database creada (testing reducido)")
    res = rag.search("What happened in 1945", k=5, verbose=True)
    print("Search completed, resultados:", len(res))
    # Cargar la DB para uso posterior
    rag.load_chroma_db(verbose=True)
    print("Database loaded")

