from __future__ import annotations

import os
from pathlib import Path
from textwrap import dedent

from dotenv import load_dotenv

from .config import MODEL_OPTIONS, TOPICS

# Load the project's .env file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


# ============================================================
# API KEY
# ============================================================

def _api_key() -> str | None:
    """
    Get the Gemini API key from environment variables.

    Supports:
    - GEMINI_API_KEY
    - EMERGENT_LLM_KEY
    """

    return (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("EMERGENT_LLM_KEY")
    )


# ============================================================
# FALLBACK REVIEW
# ============================================================

def _fallback_review(
    topic_name: str,
    issue: str,
    language: str,
) -> str:
    del topic_name, issue, language
    return (
        "### Short answer\n"
        "I couldn't generate a reliable answer just now because the answer service "
        "is temporarily unavailable.\n\n"
        "### What you can do\n"
        "- Please try your question again in a little while.\n"
        "- Keep any relevant receipts, messages, and notices so they are available "
        "when you retry.\n\n"
        "This is general legal information, not legal advice."
    )


# ============================================================
# FALLBACK DOCUMENT SUMMARY
# ============================================================

def _fallback_document_summary(
    text: str,
    language: str,
) -> str:

    preview = (
        text[:1500]
        if text
        else "No readable text was found."
    )

    return dedent(
        f"""
        ### Plain-language document summary

        The uploaded document appears to contain the following
        central material:

        {preview}

        ### Points to check

        - Parties, dates, addresses, signatures, and reference numbers.
        - Any deadline, penalty, jurisdiction, arbitration, refund,
          termination, or notice clause.
        - Any missing annexure or page referred to by the document.

        ### Risks and limitations

        - A plain summary may miss legal effects in definitions
          or cross-referenced clauses.
        - Scanned PDFs may produce incomplete text.
        - Verify important legal decisions with a qualified advocate.

        _Requested language: {language}_
        """
    ).strip()


# ============================================================
# GEMINI CLIENT
# ============================================================

def _get_gemini_client():
    """
    Create a Gemini client using the current google-genai SDK.

    IMPORTANT:
    This intentionally does NOT use:
        google.generativeai
        genai.configure()
        genai.GenerativeModel()

    The current SDK uses:
        from google import genai
        genai.Client(...)
    """

    key = _api_key()

    if not key:
        return None

    from google import genai

    return genai.Client(
        api_key=key
    )


# ============================================================
# MODEL ID
# ============================================================

def _get_model_id(
    model_label: str,
) -> str:

    if model_label not in MODEL_OPTIONS:
        model_label = next(
            iter(MODEL_OPTIONS)
        )

    return MODEL_OPTIONS[
        model_label
    ]["model_id"]


# ============================================================
# GENERATE LEGAL REVIEW
# ============================================================

# ============================================================
# GENERATE LEGAL REVIEW
# ============================================================

def generate_review(
    topic_name: str,
    issue: str,
    model_label: str,
    language: str,
    retrieved_context: str | None = None,
    conversation: list[dict] | None = None,
) -> str:

    key = _api_key()

    if not key:
        print("\n[LegaliQ] No Gemini API key found. Using fallback mode.")
        return _fallback_review(
            topic_name=topic_name,
            issue=issue,
            language=language,
        )

    try:

        client = _get_gemini_client()

        if client is None:
            print("\n[LegaliQ] Gemini client could not be created. Using fallback mode.")
            return _fallback_review(
                topic_name=topic_name,
                issue=issue,
                language=language,
            )

        model_id = _get_model_id(model_label)

        print("\n" + "=" * 70)
        print("LEGALIQ GEMINI REQUEST")
        print("=" * 70)
        print(f"Model label: {model_label}")
        print(f"Model ID: {model_id}")
        print(f"Language: {language}")
        print(f"Topic: {topic_name}")
        print(f"Retrieved context available: {bool(retrieved_context)}")
        print("=" * 70)

        topic = TOPICS.get(
            topic_name,
            TOPICS["Broad legal query"],
        )

        # ----------------------------------------------------
        # Conversation history
        # ----------------------------------------------------

        conversation_text = ""

        if conversation:

            conversation_text = "\n".join(
                f"{message.get('role', 'user')}: "
                f"{message.get('content', '')}"
                for message in conversation[-8:]
            )

        # ----------------------------------------------------
        # RAG context
        # ----------------------------------------------------

        legal_context = (
            retrieved_context
            if retrieved_context
            else "NO RETRIEVED LEGAL EVIDENCE IS AVAILABLE."
        )

        # ----------------------------------------------------
        # Prompt
        # ----------------------------------------------------

        prompt = dedent(
            f"""
            You are LegaliQ, an educational Indian legal
            information assistant.

            You are NOT a lawyer and must not present yourself
            as one.

            Your purpose is to provide clear, simple,
            evidence-grounded legal information to citizens.

            ====================================================
            LANGUAGE
            ====================================================

            Respond in {language}.

            ====================================================
            MOST IMPORTANT RULE: USE THE RETRIEVED EVIDENCE
            ====================================================

            The section called:

            "RETRIEVED LEGAL EVIDENCE FROM LEGALIQ KNOWLEDGE BASE"

            contains evidence retrieved from the project's
            legal knowledge base.

            Treat this retrieved evidence as the PRIMARY SOURCE
            for legal claims.

            Use the retrieved evidence to answer the user's
            question.

            Do NOT simply give a generic answer based on your
            general knowledge.

            If the retrieved evidence does not support a claim,
            do not present that claim as established law.

            If the retrieved evidence is insufficient to answer
            an important part of the question, clearly say:

            "The available legal evidence in the knowledge base
            is insufficient to establish this point."

            Do not invent missing information.

            ====================================================
            LEGAL SAFETY RULES
            ====================================================

            1. Do not invent sections, articles, regulations,
               rules, cases, authorities, deadlines, penalties,
               procedures, or citations.

            2. Do not create fake legal citations.

            3. Do not claim that a specific legal remedy is
               guaranteed.

            4. Do not present an inference as if it were a
               quotation from legislation.

            5. Do not invent facts that the user did not provide.

            6. Clearly distinguish retrieved legal information
               from general practical suggestions.

            7. When referring to retrieved material, identify
               the document and page whenever that information
               is available.

            8. If different retrieved sources do not clearly
               answer the question, acknowledge the limitation.

            9. Use simple language suitable for an ordinary
               citizen.

            10. Do not overwhelm the user with unnecessary
                legal terminology.

            ====================================================
            USER QUESTION
            ====================================================

            {issue}

            ====================================================
            SELECTED TOPIC
            ====================================================

            {topic.name}

            ====================================================
            EXISTING CONVERSATION
            ====================================================

            {conversation_text or "No previous conversation."}

            ====================================================
            RETRIEVED LEGAL EVIDENCE FROM LEGALIQ KNOWLEDGE BASE
            ====================================================

            {legal_context}

            ====================================================
            GENERAL TOPIC REFERENCE
            ====================================================

            The following information describes the selected
            application topic.

            It is NOT a substitute for the retrieved legal
            evidence above.

            Topic reference:

            {topic.article}

            Source direction:

            {topic.source}

            ====================================================
            RESPONSE INSTRUCTIONS
            ====================================================

            Answer the user's actual question.

            Use the retrieved legal evidence rather than giving
            a generic legal response.

            Where the retrieved evidence contains a relevant
            provision, explain it in plain language.

            Mention the document name and page number when
            available.

            If a retrieved source is only partially relevant,
            do not pretend that it establishes more than it does.

            If the evidence does not answer the question,
            explicitly state that limitation.

            ====================================================
            REQUIRED RESPONSE FORMAT
            ====================================================

            Use this format:

            ### Short answer
            Answer the user's question directly in 1-3 sentences.

            ### What you can do
            Give up to 3 practical, numbered next steps. Keep
            each step short and relevant to the question.

            ### Important to know
            Include this only when a real limitation, risk, or
            missing fact matters. Ask at most one brief follow-up
            question only if its answer could change the guidance.

            Keep the complete answer under 180 words. Use everyday
            language and short sentences. Do not add a generic
            disclaimer heading, repeat the question, draft a
            complaint letter, or include a long evidence checklist.
            The interface adds the legal-information disclaimer
            and clickable source links separately.

            Cite a retrieved document or page only when it appears
            in the retrieved evidence. Do not invent citations or
            web links.

            ====================================================
            FINAL GROUNDING CHECK
            ====================================================

            Before answering, check every important legal claim.

            If the claim is not supported by the retrieved
            evidence, either remove it or clearly identify it
            as general information rather than established
            information from the knowledge base.

            Never fabricate a citation or legal provision.
            """
        )

        # ----------------------------------------------------
        # DEBUG INFORMATION
        # ----------------------------------------------------

        print("\n[LegaliQ] Sending RAG-grounded prompt to Gemini...")
        print(f"[LegaliQ] Prompt length: {len(prompt)} characters")
        print(f"[LegaliQ] Retrieved context length: {len(legal_context)} characters")

        # ----------------------------------------------------
        # GEMINI GENERATION
        # ----------------------------------------------------

        response = None
        models_to_try = [model_id]
        if model_id != "gemini-2.5-flash":
            models_to_try.append("gemini-2.5-flash")

        for attempt, candidate_model in enumerate(models_to_try):
            try:
                response = client.models.generate_content(
                    model=candidate_model,
                    contents=prompt,
                    config={
                        "max_output_tokens": 500,
                        "temperature": 0.3,
                    },
                )
                break
            except Exception as exc:
                if attempt == len(models_to_try) - 1:
                    raise
                print(
                    "[LegaliQ] Primary Gemini model failed "
                    f"({type(exc).__name__}); retrying with "
                    f"{models_to_try[attempt + 1]}."
                )

        if response is None:
            raise RuntimeError("Gemini returned no response.")

        result = getattr(
            response,
            "text",
            None,
        )

        if not result:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        print("\n[LegaliQ] Gemini response received successfully.")

        return result.strip()

    except Exception as exc:

        print("\n" + "=" * 70)
        print("GEMINI ERROR")
        print("=" * 70)
        print(f"Error type: {type(exc).__name__}")
        print(f"Error message: {exc}")
        print("=" * 70)

        return _fallback_review(
            topic_name=topic_name,
            issue=issue,
            language=language,
        )

# ============================================================
# SUMMARIZE DOCUMENT
# ============================================================

def summarize_document(
    text: str,
    filename: str,
    model_label: str,
    language: str,
) -> str:

    key = _api_key()

    if not key:

        return _fallback_document_summary(
            text=text,
            language=language,
        )

    try:

        client = _get_gemini_client()

        if client is None:

            return _fallback_document_summary(
                text=text,
                language=language,
            )

        model_id = _get_model_id(
            model_label
        )

        prompt = dedent(
            f"""
            You are LegaliQ, an educational Indian legal
            information assistant.

            You are NOT a lawyer.

            Summarize the uploaded legal document in
            {language}.

            Do not provide final legal advice.

            Do not invent information that does not appear
            in the document.

            ====================================================
            FILE
            ====================================================

            {filename}

            ====================================================
            DOCUMENT TEXT
            ====================================================

            {text}

            ====================================================
            REQUIRED FORMAT
            ====================================================

            ### Plain-language summary

            Explain the document simply.

            ### Key parties

            Identify important parties if clearly stated.

            ### Important dates and deadlines

            Mention dates or deadlines explicitly present
            in the document.

            ### Important obligations

            Explain important duties or responsibilities.

            ### Relevant clauses/articles

            Identify important clauses, sections, or articles.

            ### Risks or limitations

            Identify important limitations, conditions,
            exceptions, or risks.

            ### Evidence or missing documents

            Mention documents that appear to be relevant
            or missing.

            ### Questions to ask a lawyer or authority

            Provide useful questions based only on the document.
            """
        )

        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
        )

        result = getattr(
            response,
            "text",
            None,
        )

        if not result:

            raise RuntimeError(
                "Gemini returned an empty document summary."
            )

        return result.strip()

    except Exception as exc:

        print("\n" + "=" * 70)
        print("GEMINI DOCUMENT SUMMARY ERROR")
        print("=" * 70)
        print(
            f"Error type: {type(exc).__name__}"
        )
        print(
            f"Error message: {exc}"
        )
        print("=" * 70)

        return (
            _fallback_document_summary(
                text=text,
                language=language,
            )
            + "\n\n"
            + "_AI provider unavailable. "
            + "Technical detail: "
            + f"{type(exc).__name__}: {exc}_"
        )


# ============================================================
# FOLLOW-UP QUESTION
# ============================================================

def answer_follow_up(
    topic_name: str,
    history: list[dict],
    question: str,
    model_label: str,
    language: str,
) -> str:

    key = _api_key()

    if not key:

        return dedent(
            f"""
            I have added your update to this review.

            For **{topic_name}**, connect every new fact
            to a date, supporting proof, and next action.

            ### Your new question

            {question}

            ### Suggested next step

            Preserve the relevant evidence, avoid changing
            or deleting original records, check important
            deadlines, and verify the applicable legal forum
            before filing anything.

            Share what you have already done, any acknowledgement
            numbers, and the date of the latest event so that
            the guidance can become more precise.
            """
        ).strip()

    try:

        client = _get_gemini_client()

        if client is None:

            return dedent(
                f"""
                I could not connect to the AI provider.

                Your follow-up question was:

                {question}

                Please preserve your evidence and verify
                important deadlines with an official source
                or qualified lawyer.
                """
            ).strip()

        model_id = _get_model_id(
            model_label
        )

        transcript = "\n".join(
            f"{message.get('role', 'user')}: "
            f"{message.get('content', '')}"
            for message in history[-10:]
        )

        prompt = dedent(
            f"""
            You are LegaliQ, an educational Indian legal
            information assistant.

            You are NOT a lawyer.

            Respond in {language}.

            Continue the user's existing legal-information
            conversation.

            Do not guarantee a legal outcome.

            Do not invent legal provisions or citations.

            Give practical next steps and identify evidence
            that should be preserved.

            ====================================================
            TOPIC
            ====================================================

            {topic_name}

            ====================================================
            EXISTING CONVERSATION
            ====================================================

            {transcript}

            ====================================================
            USER FOLLOW-UP
            ====================================================

            {question}

            ====================================================
            RESPONSE FORMAT
            ====================================================

            ### Answer

            Answer the user's question clearly.

            ### What this changes

            Explain how the new information affects the
            previous discussion, if applicable.

            ### Next steps

            Give practical next actions.

            ### Evidence to preserve

            List useful evidence.

            ### Important limitation

            Mention any important uncertainty or missing fact.

            Keep the answer understandable and concise.
            """
        )

        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
        )

        result = getattr(
            response,
            "text",
            None,
        )

        if not result:

            raise RuntimeError(
                "Gemini returned an empty follow-up response."
            )

        return result.strip()

    except Exception as exc:

        print("\n" + "=" * 70)
        print("GEMINI FOLLOW-UP ERROR")
        print("=" * 70)
        print(
            f"Error type: {type(exc).__name__}"
        )
        print(
            f"Error message: {exc}"
        )
        print("=" * 70)

        return (
            "I could not reach the AI provider right now, "
            "but your follow-up was received. Please preserve "
            "your evidence and verify important deadlines "
            "and legal sources before taking formal action.\n\n"
            f"Technical detail: {type(exc).__name__}: {exc}"
        )