import unittest
from unittest.mock import MagicMock, patch, mock_open
import numpy as np
from project.rag import RAG

class DummyEmbedding:
    def __init__(self, values):
        self.values = values

class DummyEmbedContentResult:
    def __init__(self, embeddings):
        self.embeddings = embeddings

class DummyClient:
    class models:
        @staticmethod
        def embed_content(model, contents, config):
            # Return as many embeddings as contents
            return DummyEmbedContentResult([DummyEmbedding([float(i)]*3) for i in range(len(contents))])

class DummyVectorDB:
    def __init__(self):
        self.data = []
    def add(self, chunk, embedding):
        self.data.append((chunk, embedding))
    def save(self, path):
        self.saved_path = path
    def load(self, path):
        self.loaded_path = path
    def search(self, query_embedding, k=5):
        return [("chunk", 0.99)] * k

@patch("project.rag.VectorDB", DummyVectorDB)
@patch("project.rag.RecursiveCharacterTextSplitter")
class TestRAG(unittest.TestCase):
    def setUp(self):
        self.dummy_client = DummyClient()
        self.rag = RAG(dir="dummy_dir", client=self.dummy_client)

    @patch("os.listdir", return_value=["file1.txt", "file2.txt"])
    @patch("builtins.open", new_callable=mock_open, read_data="test content")
    def test_reader_reads_txt_files(self, mock_file, mock_listdir, mock_splitter):
        self.rag.text = ""
        result = self.rag.reader()
        self.assertIn("test content", result)
        self.assertTrue(result.endswith("\n"))

    def test_chunker_splits_text(self, mock_splitter):
        self.rag.text = "a" * 200
        instance = mock_splitter.return_value
        instance.split_text.return_value = ["chunk1", "chunk2"]
        chunks = self.rag.chunker(chunk_size=100)
        self.assertEqual(chunks, ["chunk1", "chunk2"])
        mock_splitter.assert_called_once()

    def test_embedder_returns_embeddings(self, mock_splitter):
        texts = ["text1", "text2"]
        embeddings = self.rag.embedder(texts)
        self.assertEqual(len(embeddings), 2)
        self.assertTrue(isinstance(embeddings[0], np.ndarray))

    @patch.object(RAG, "reader")
    @patch.object(RAG, "chunker")
    @patch.object(RAG, "embedder")
    def test_create_database(self, mock_embedder, mock_chunker, mock_reader, mock_splitter):
        rag = RAG(dir="dummy_dir", client=self.dummy_client)  # Needed to patch with VectorDB

        mock_reader.return_value = "some text"
        mock_chunker.return_value = ["chunk1", "chunk2"]
        mock_embedder.return_value = [np.array([1,2,3]), np.array([4,5,6])]

        db = rag.create_database()
        self.assertIsInstance(db, DummyVectorDB)

    def test_save_database_calls_save(self, mock_splitter):
        self.rag.vector_db.save = MagicMock()
        self.rag.save_database("test.pkl")
        self.rag.vector_db.save.assert_called_once()
        self.assertTrue(self.rag.vector_db.save.call_args[0][0].endswith("test.pkl"))

    def test_load_database_calls_load(self, mock_splitter):
        self.rag.vector_db.load = MagicMock()
        self.rag.load_database("test.pkl")
        self.rag.vector_db.load.assert_called_once()
        self.assertTrue(self.rag.vector_db.load.call_args[0][0].endswith("test.pkl"))

    def test_search_returns_results(self, mock_splitter):
        self.rag.embedder = MagicMock(return_value=[np.array([1,2,3])])
        self.rag.vector_db.search = MagicMock(return_value=[("chunk", 0.99)])
        results = self.rag.search(["query"], k=1)
        self.assertEqual(results, [("chunk", 0.99)])

if __name__ == "__main__":
    unittest.main()