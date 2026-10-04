from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from legaliq.ai import generate_review
from legaliq.rag import answer_with_rag


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_LABEL = "Gemini 2.5 Flash"
LANGUAGE = "English"

OUTPUT_FILE = Path("rag_vs_llm_results.csv")


# ============================================================
# TEST QUESTIONS
# ============================================================

TEST_QUESTIONS = [
    {
        "id": "Q1",
        "topic": "Consumer rights",
        "question": (
            "I bought a defective product online and the seller is "
            "refusing to provide a refund. What can I do?"
        ),
    },
    {
        "id": "Q2",
        "topic": "Consumer rights",
        "question": (
            "An online shopping website used a misleading discount and "
            "showed a much higher price before applying the discount. "
            "What consumer rights may be relevant?"
        ),
    },
    {
        "id": "Q3",
        "topic": "Consumer rights",
        "question": (
            "An e-commerce website added an unwanted product to my cart "
            "without clearly asking for my permission. Is this something "
            "I can complain about?"
        ),
    },
    {
        "id": "Q4",
        "topic": "Consumer rights",
        "question": (
            "A seller advertised a product with a guarantee but later "
            "refused to honour the promised guarantee. What should I do?"
        ),
    },
    {
        "id": "Q5",
        "topic": "Consumer rights",
        "question": (
            "A product caused harm after I purchased it. Can the "
            "manufacturer or seller be held responsible?"
        ),
    },
]


# ============================================================
# LLM-ONLY
# ============================================================

def run_llm_only(question_data: dict) -> str:

    print("\n" + "=" * 70)
    print("RUNNING LLM-ONLY")
    print("=" * 70)

    print("Question:")
    print(question_data["question"])

    answer = generate_review(
        topic_name=question_data["topic"],
        issue=question_data["question"],
        model_label=MODEL_LABEL,
        language=LANGUAGE,
        retrieved_context=None,
        conversation=[],
    )

    return answer


# ============================================================
# RAG
# ============================================================

def run_rag(question_data: dict) -> dict:

    print("\n" + "=" * 70)
    print("RUNNING RAG")
    print("=" * 70)

    print("Question:")
    print(question_data["question"])

    result = answer_with_rag(
        topic_name=question_data["topic"],
        question=question_data["question"],
        model_label=MODEL_LABEL,
        language=LANGUAGE,
        history=[],
    )

    return result


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(results: list[dict]):

    fieldnames = [
        "question_id",
        "question",
        "topic",
        "llm_only_response",
        "rag_response",
        "retrieved_chunks",
        "sources",
        "timestamp",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for result in results:
            writer.writerow(result)

    print("\n" + "=" * 70)
    print("RESULTS SAVED")
    print("=" * 70)

    print(f"File: {OUTPUT_FILE.resolve()}")


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 70)
    print("LEGALIQ RAG vs LLM EVALUATION")
    print("=" * 70)

    print(f"Model: {MODEL_LABEL}")
    print(f"Language: {LANGUAGE}")
    print(f"Questions: {len(TEST_QUESTIONS)}")

    results = []

    for index, question_data in enumerate(
        TEST_QUESTIONS,
        start=1,
    ):

        print("\n")
        print("#" * 70)
        print(
            f"QUESTION {index}/{len(TEST_QUESTIONS)}"
        )
        print("#" * 70)

        print(question_data["question"])

        # ----------------------------------------------------
        # LLM ONLY
        # ----------------------------------------------------

        llm_answer = run_llm_only(
            question_data
        )

        # ----------------------------------------------------
        # RAG
        # ----------------------------------------------------

        rag_result = run_rag(
            question_data
        )

        rag_answer = rag_result.get(
            "answer",
            "",
        )

        retrieved_chunks = rag_result.get(
            "retrieved_chunks",
            0,
        )

        sources = rag_result.get(
            "sources",
            [],
        )

        source_text = "; ".join(
            f"{source.get('title', 'Unknown')} "
            f"(page {source.get('page', 'Unknown')})"
            for source in sources
        )

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        results.append(
            {
                "question_id": question_data["id"],
                "question": question_data["question"],
                "topic": question_data["topic"],
                "llm_only_response": llm_answer,
                "rag_response": rag_answer,
                "retrieved_chunks": retrieved_chunks,
                "sources": source_text,
                "timestamp": datetime.now().isoformat(),
            }
        )

        print("\n")
        print("-" * 70)
        print("LLM-ONLY RESPONSE")
        print("-" * 70)
        print(llm_answer)

        print("\n")
        print("-" * 70)
        print("RAG RESPONSE")
        print("-" * 70)
        print(rag_answer)

        print("\n")
        print("-" * 70)
        print("RETRIEVED CHUNKS")
        print("-" * 70)
        print(retrieved_chunks)

    save_results(results)

    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()