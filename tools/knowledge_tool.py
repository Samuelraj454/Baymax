import os
from typing import Dict, Any, List
from .base_tool import BaseTool, ToolResult
from loguru import logger
from memory.vector_store import VectorStore
import uuid

class KnowledgeTool(BaseTool):
    """
    Tool for reading files (txt, md) and storing them in the persistent Vector Store,
    and searching the vector store for RAG.
    """
    name = "knowledge_tool"
    description = "Use this to 'learn_file' to store a text/markdown file into long-term vector memory, or 'search_knowledge' to query the vector database for answers."
    
    def __init__(self):
        super().__init__()
        self.vector_store = VectorStore()

    def run(self, **params) -> ToolResult:
        action = params.get("action")
        
        if action == "learn_file":
            filepath = params.get("filepath", "")
            if not os.path.exists(filepath):
                return ToolResult(success=False, output="", error=f"File not found at {filepath}")
                
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic chunking (very simple split by paragraphs)
                chunks = [c.strip() for c in content.split('\n\n') if len(c.strip()) > 20]
                
                count = 0
                for chunk in chunks:
                    doc_id = str(uuid.uuid4())
                    self.vector_store.store(doc_id, chunk, {"source": filepath})
                    count += 1
                    
                return ToolResult(success=True, output=f"Successfully learned {count} chunks of knowledge from {filepath}.")
            except Exception as e:
                logger.error(f"Error reading {filepath}: {e}")
                return ToolResult(success=False, output="", error=f"Error learning file: {e}")
                
        elif action == "search_knowledge":
            query = params.get("query", "")
            if not query:
                return ToolResult(success=False, output="", error="No query provided.")
                
            results = self.vector_store.search(query, top_k=3)
            if not results:
                return ToolResult(success=True, output="No relevant knowledge found in the database.")
                
            response_lines = ["Found the following relevant knowledge:"]
            for i, res in enumerate(results):
                source = res.get('metadata', {}).get('source', 'unknown')
                response_lines.append(f"\n--- Result {i+1} (Source: {source}) ---")
                response_lines.append(res['text'])
                
            return ToolResult(success=True, output="\n".join(response_lines))
            
        else:
            return ToolResult(success=False, output="", error="Unknown action. Must be 'learn_file' or 'search_knowledge'.")

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["learn_file", "search_knowledge"],
                            "description": "The action to perform."
                        },
                        "filepath": {
                            "type": "string",
                            "description": "The absolute path to the file to learn (only if action is 'learn_file')."
                        },
                        "query": {
                            "type": "string",
                            "description": "The search query to search the knowledge base for (only if action is 'search_knowledge')."
                        }
                    },
                    "required": ["action"]
                }
            }
        }
