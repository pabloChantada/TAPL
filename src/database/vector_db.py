import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity

class VectorDB:
    def __init__(self):
        self.embeddings = []
        self.chunks = []

    def add(self, chunk, embedding):
        self.chunks.append(chunk)
        self.embeddings.append(embedding)

    def search(self, query_embedding, k=5):
        if not self.embeddings:
            return []
        
        # Convert to numpy arrays 
        embeddings_array = np.array(self.embeddings)
        query_array = np.array(query_embedding)

        # Reshape query_array to 2D to compute cosine similarity, and flatten the result
        similarities = cosine_similarity(embeddings_array, query_array.reshape(1, -1)).flatten()
        
        # Top k docs
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        results = []
        for idx in top_k_indices:
            results.append({
                'chunk': self.chunks[idx],
                'similarity': similarities[idx],
                'index': idx
            })
        return results
    
    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump({'chunks': self.chunks, 'embeddings': self.embeddings}, f)
    
    def load(self, path):
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.chunks = data['chunks']
            self.embeddings = data['embeddings']

    