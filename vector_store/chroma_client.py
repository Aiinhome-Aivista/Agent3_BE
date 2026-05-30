"""ChromaDB Client - Handles connection and operations with Chroma Vector Database."""

import os
import chromadb
from chromadb.config import Settings
import logging

logger = logging.getLogger(__name__)

class ChromaClient:
    def __init__(self):
        self.persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        try:
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            logger.info(f"Connected to ChromaDB at {self.persist_directory}")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            self.client = None

    def get_or_create_collection(self, collection_name: str):
        if not self.client:
            return None
        try:
            return self.client.get_or_create_collection(name=collection_name)
        except Exception as e:
            logger.error(f"Error getting/creating collection {collection_name}: {e}")
            return None

    def add_documents(self, collection_name: str, documents: list, metadatas: list, ids: list):
        collection = self.get_or_create_collection(collection_name)
        if collection:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(ids)} documents to {collection_name}")

    def query(self, collection_name: str, query_texts: list, n_results: int = 5):
        collection = self.get_or_create_collection(collection_name)
        if collection:
            return collection.query(
                query_texts=query_texts,
                n_results=n_results
            )
        return None

# Singleton instance
chroma_db = ChromaClient()
