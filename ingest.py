from __future__ import annotations

from pathlib import Path

from legaliq.config import KNOWLEDGE_BASE_DIR
from legaliq.documents import create_legal_chunks
from legaliq.embeddings import embed_texts
from legaliq.vector_store import add_documents


def main():

    KNOWLEDGE_BASE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pdf_files = list(
        KNOWLEDGE_BASE_DIR.glob("*.pdf")
    )

    if not pdf_files:
        print(
            "No PDF files found in knowledge_base/"
        )
        return

    all_chunks = []

    print(
        f"Found {len(pdf_files)} legal PDF(s)."
    )

    for pdf_path in pdf_files:

        print(
            f"\nProcessing: {pdf_path.name}"
        )

        chunks = create_legal_chunks(
            pdf_path
        )

        print(
            f"Created {len(chunks)} chunks."
        )

        all_chunks.extend(chunks)

    if not all_chunks:
        print(
            "No readable legal text was extracted."
        )
        return

    texts = [
        item["text"]
        for item in all_chunks
    ]

    metadatas = [
        item["metadata"]
        for item in all_chunks
    ]

    ids = [
        (
            f"{metadata['filename']}"
            f"_page_{metadata['page']}"
            f"_chunk_{metadata['chunk']}"
        )
        for metadata in metadatas
    ]

    print(
        f"\nGenerating embeddings for "
        f"{len(texts)} chunks..."
    )

    embeddings = embed_texts(texts)

    print(
        "\nSaving chunks to ChromaDB..."
    )

    count = add_documents(
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )

    print(
        f"\nSUCCESS: Vector database now contains "
        f"{count} chunks."
    )


if __name__ == "__main__":
    main()