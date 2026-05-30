"""ArangoDB Client - Handles connection and operations with Arango Graph Database."""

import os
from arango import ArangoClient
import logging

logger = logging.getLogger(__name__)

class ArangoGraphClient:
    def __init__(self):
        self.host = os.getenv("ARANGO_HOST", "http://localhost:8529")
        self.db_name = os.getenv("ARANGO_DB", "dq_lineage")
        self.username = os.getenv("ARANGO_USER", "root")
        self.password = os.getenv("ARANGO_PASSWORD", "")
        
        try:
            # Initialize the client
            self.client = ArangoClient(hosts=self.host)
            # Connect to database
            self.db = self.client.db(self.db_name, username=self.username, password=self.password)
            logger.info(f"Connected to ArangoDB at {self.host}")
        except Exception as e:
            logger.error(f"Failed to connect to ArangoDB: {e}")
            self.db = None

    def get_or_create_collection(self, collection_name: str, edge: bool = False):
        if not self.db:
            return None
        if self.db.has_collection(collection_name):
            return self.db.collection(collection_name)
        else:
            if edge:
                return self.db.create_collection(collection_name, edge=True)
            else:
                return self.db.create_collection(collection_name)

    def insert_node(self, collection_name: str, node_data: dict):
        col = self.get_or_create_collection(collection_name)
        if col:
            try:
                return col.insert(node_data)
            except Exception as e:
                logger.error(f"Error inserting node into {collection_name}: {e}")
        return None

    def insert_edge(self, edge_collection: str, from_node: str, to_node: str, edge_data: dict = None):
        col = self.get_or_create_collection(edge_collection, edge=True)
        if col:
            data = {"_from": from_node, "_to": to_node}
            if edge_data:
                data.update(edge_data)
            try:
                return col.insert(data)
            except Exception as e:
                logger.error(f"Error inserting edge into {edge_collection}: {e}")
        return None

    def query(self, aql: str, bind_vars: dict = None):
        if not self.db:
            return None
        try:
            cursor = self.db.aql.execute(aql, bind_vars=bind_vars)
            return [doc for doc in cursor]
        except Exception as e:
            logger.error(f"Error executing AQL: {e}")
            return None

# Singleton instance
arango_db = ArangoGraphClient()
