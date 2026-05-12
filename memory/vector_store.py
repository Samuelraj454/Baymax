import chromadb
from chromadb.utils import embedding_functions
from app_config import CHROMA_PATH
import os

class VectorStore:
    def __init__(self):
        os.makedirs(CHROMA_PATH, exist_ok=True)
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="baymax_memory",
            embedding_function=self.ef
        )

    def store(self, doc_id: str, text: str, metadata: dict = None):
        self.collection.upsert(
            documents=[text],
            metadatas=[metadata] if metadata else [{}],
            ids=[doc_id]
        )

    def search(self, query: str, top_k: int = 5) -> list:
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        parsed_results = []
        if not results["ids"]:
            return parsed_results
            
        for i in range(len(results["ids"][0])):
            parsed_results.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if "distances" in results else 0.0
            })
        return parsed_results

    def delete(self, doc_id: str):
        self.collection.delete(ids=[doc_id])
