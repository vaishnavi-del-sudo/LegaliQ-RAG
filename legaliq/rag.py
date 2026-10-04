from __future__ import annotations

from .config import TOP_K_RESULTS
from .embeddings import embed_query
from .vector_store import search
from .ai import generate_review


# ============================================================
# RETRIEVE LEGAL EVIDENCE
# ============================================================

def retrieve_legal_context(question: str, top_k: int = TOP_K_RESULTS):
    if not question or not question.strip():
        return []

    query_embedding = embed_query(question.strip())

    results = search(
        query_embedding=query_embedding,
        top_k=top_k
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved = []

    for index, document in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        distance = distances[index] if index < len(distances) else None

        retrieved.append({
            "text": document,
            "metadata": metadata,
            "distance": distance,
        })

    # ---------------------------------------------------------
    # Relevance check
    # Lower Chroma distance = stronger semantic match.
    # ---------------------------------------------------------

    if not retrieved:
        return []

    valid_distances = [
        item["distance"]
        for item in retrieved
        if item["distance"] is not None
    ]

    if not valid_distances:
        return retrieved

    best_distance = min(valid_distances)

    RELEVANCE_THRESHOLD = 1.0

    print(
        f"[LegaliQ] Best retrieval distance: "
        f"{best_distance:.4f}"
    )

    if best_distance > RELEVANCE_THRESHOLD:
        print(
            "[LegaliQ] No sufficiently relevant legal evidence "
            "was found in the knowledge base."
        )
        return []

    return retrieved
# ============================================================
# BUILD LLM CONTEXT
# ============================================================

def build_context(
    retrieved_chunks: list[dict],
) -> str:
    """
    Convert retrieved ChromaDB chunks into a clean context
    string that can be passed to the Gemini prompt.
    """

    if not retrieved_chunks:
        return (
            "NO LEGAL EVIDENCE WAS RETRIEVED "
            "FROM THE LEGALIQ KNOWLEDGE BASE."
        )

    parts = []

    for index, item in enumerate(
        retrieved_chunks,
        start=1,
    ):

        metadata = item.get(
            "metadata",
            {},
        )

        # Support both possible metadata names.
        source = (
            metadata.get("source")
            or metadata.get("filename")
            or "Unknown source"
        )

        page = metadata.get(
            "page",
            "Unknown",
        )

        chunk = metadata.get(
            "chunk",
            "Unknown",
        )

        distance = item.get(
            "distance"
        )

        distance_text = ""

        if distance is not None:
            distance_text = (
                f"\nRetrieval distance: "
                f"{distance:.4f}"
            )

        parts.append(
            f"""
SOURCE {index}
Document: {source}
Page: {page}
Chunk: {chunk}
{distance_text}

Legal text:
{item["text"]}
""".strip()
        )

    return "\n\n---\n\n".join(parts)


# ============================================================
# BUILD SOURCES FOR UI
# ============================================================

def _official_source_url(
    source: str,
    metadata: dict,
) -> str:
    metadata_url = metadata.get("source_url") or metadata.get("url")
    if isinstance(metadata_url, str) and metadata_url.startswith("https://"):
        return metadata_url

    normalized_source = source.casefold()
    if "act" in normalized_source and (
        "consumer" in normalized_source or "cp act" in normalized_source
    ):
        return "https://www.indiacode.nic.in/"

    return "https://consumeraffairs.gov.in/"


def build_sources(
    retrieved_chunks: list[dict],
) -> list[dict]:
    """
    Prepare source information that can later be displayed
    underneath the LegaliQ answer.

    This is useful for demonstrating RAG to your supervisor:
    the user can see which PDF/page contributed to the answer.
    """

    sources = []

    sources_by_title = {}

    for item in retrieved_chunks:

        metadata = item.get(
            "metadata",
            {},
        )

        source = (
            metadata.get("source")
            or metadata.get("filename")
            or "Unknown source"
        )

        page = metadata.get(
            "page"
        )

        if source not in sources_by_title:
            sources_by_title[source] = {
                "title": source,
                "page": page,
                "pages": [],
                "url": _official_source_url(source, metadata),
                "distance": item.get(
                    "distance"
                ),
            }
            sources.append(sources_by_title[source])

        source_entry = sources_by_title[source]
        if page is not None and page not in source_entry["pages"]:
            source_entry["pages"].append(page)

    return sources


# ============================================================
# COMPLETE RAG ANSWER
# ============================================================

def answer_with_rag(topic_name, question, model_label, language, history=None):
    retrieved = retrieve_legal_context(question=question)

    # No sufficiently relevant evidence was found.
    # Do not send an unsupported question to the LLM.
    if not retrieved:
        print(
            "[LegaliQ] No relevant legal evidence found. "
            "Skipping Gemini."
        )

        answer = (
            "### Short answer\n"
            "I couldn't find enough relevant information in the "
            "LegaliQ knowledge base to answer this reliably.\n\n"
            "### Next step\n"
            "Try rephrasing your question or ask about consumer rights, "
            "e-commerce, or direct selling."
        )

        return {
            "answer": answer,
            "sources": [],
            "retrieved_chunks": 0,
        }

    context = build_context(retrieved)
    sources = build_sources(retrieved)

    answer = generate_review(
        topic_name=topic_name,
        issue=question,
        model_label=model_label,
        language=language,
        retrieved_context=context,
        conversation=history or [],
    )

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": len(retrieved),
    }