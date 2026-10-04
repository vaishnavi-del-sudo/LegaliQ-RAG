from __future__ import annotations

from pathlib import Path

import chromadb

from .config import VECTOR_DB_DIR, VECTOR_COLLECTION_NAME


def get_collection():

    Path(VECTOR_DB_DIR).mkdir(
        parents=True,
        exist_ok=True,
    )

    client = chromadb.PersistentClient(
        path=str(VECTOR_DB_DIR)
    )

    collection = client.get_or_create_collection(
        name=VECTOR_COLLECTION_NAME,
        metadata={
            "description": "LegaliQ Indian legal knowledge base"
        },
    )

    return collection


def add_documents(
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    ids: list[str],
):

    collection = get_collection()

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return collection.count()


def search(
    query_embedding: list[float],
    top_k: int = 5,
):

    collection = get_collection()

    if collection.count() == 0:
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

    return collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )