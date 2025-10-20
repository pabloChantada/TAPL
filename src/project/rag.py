import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from google.genai import types
import numpy as np
from database.vector_db import VectorDB

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "database")
API_KEY=os.getenv('GEMINI_API_KEY')

class RAG:
    def __init__(self, dir, client, model="gemini-embedding-001") -> None:
        self.dir = dir
        self.client = client
        self.model = model
        self.text = ""
        self.vector_db = VectorDB()
        self.MODEL_EMBEDDER = os.getenv('MODEL_EMBEDDER')
        
    def reader(self):
        """Leer todos los archivos de texto en la carpeta database"""
        for file in os.listdir(DB_DIR):
            if file.endswith(".txt"):
                with open(os.path.join(DB_DIR, file), "r", encoding="utf-8") as f:
                    self.text += f.read() + "\n"

        return self.text

    
    def chunker(self, chunk_size=512):
        """Dividir el texto en chunks"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=256,
            length_function=len,
            add_start_index=True,
        )
        chunks = splitter.split_text(self.text)
        return chunks
    
    def embedder(self, texts):
        """Crear embeddings para una lista de textos"""
        # Convertir a numpy arrays para el manejo
        embeddings = [
            np.array(e.values) for e in self.client.models.embed_content(
                model=self.MODEL_EMBEDDER,
                contents=texts, 
                config=types.EmbedContentConfig(task_type="QUESTION_ANSWERING")).embeddings
        ]
        
        return embeddings
    
    def create_database(self):
        """Crear la base de datos vectorial completa"""
        # Leer el archivo
        self.reader()
        print(f"Texto leído: {len(self.text)} caracteres\n")
        
        # Crear chunks
        chunks = self.chunker()
        print(f"Chunks creados: {len(chunks)}\n")
        
        # Crear embeddings
        print("Generando embeddings...")
        embeddings = self.embedder(chunks)
        print(f"Embeddings generados: {len(embeddings)}\n")
        
        for chunks, embeddings in zip(chunks, embeddings):
            # Añadir a la base de datos
            self.vector_db.add(chunks, embeddings)
        
        return self.vector_db
    
    def save_database(self, filename="vector_db.pkl"):
        """Guardar la base de datos"""
        path = os.path.join(DB_DIR, filename)
        self.vector_db.save(path)
    
    def load_database(self, filename="vector_db.pkl"):
        """Cargar la base de datos"""
        path = os.path.join(DB_DIR, filename)
        self.vector_db.load(path)
    
    def search(self, query, k=5):
        """Buscar chunks similares a una query"""
        # Obtener embedding (solo el primero si es una query simple)
        query_embedding = self.embedder(query)
        # Buscar en la base de datos
        results = self.vector_db.search(query_embedding, k=k)
        print(f"Chunks similares encontrados: {len(results)}\n")    
        return results



