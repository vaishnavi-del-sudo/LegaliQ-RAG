from legaliq.rag import answer_with_rag


print("=" * 70)
print("                 LEGALIQ RAG CHAT")
print("=" * 70)
print("Type your legal question below.")
print("Type 'exit' to stop.")
print("=" * 70)

conversation = []

while True:
    question = input("\nYou: ").strip()

    if question.lower() in ["exit", "quit"]:
        print("\nLegaliQ: Goodbye!")
        break

    if not question:
        continue

    print("\nLegaliQ is searching the legal knowledge base...")

    result = answer_with_rag(
        topic_name="Broad legal query",
        question=question,
        model_label="Gemini 3.8 Flash",
        language="English",
        history=conversation,
    )

    print("\n" + "-" * 70)
    print("LEGALIQ:")
    print("-" * 70)
    print(result["answer"])

    print("\n" + "-" * 70)
    print("SOURCES USED:")
    print("-" * 70)

    for source in result["sources"]:
        print(
            f"\nDocument: {source['title']}"
            f"\nPage: {source['page']}"
            f"\nChunk: {source['chunk']}"
            f"\nDistance: {source['distance']}"
        )

    print("\n" + "=" * 70)

    conversation.append({
        "role": "user",
        "content": question
    })

    conversation.append({
        "role": "assistant",
        "content": result["answer"]
    })