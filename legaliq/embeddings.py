from __future__ import annotations

from sentence_transformers import SentenceTransformer

from .config import EMBEDDING_MODEL


_model = None


def get_embedding_model():
    global _model

    if _model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)

    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    model = get_embedding_model()

    embedding = model.encode(
        [query],
        normalize_embeddings=True,
    )

    return embedding[0].tolist()