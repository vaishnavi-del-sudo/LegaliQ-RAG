from __future__ import annotations

import re

import streamlit as st

from legaliq.ai import answer_follow_up, generate_review, summarize_document
from legaliq.config import LANGUAGES, MODEL_OPTIONS, TOPICS
from legaliq.database import (
    add_document,
    add_message,
    add_review,
    create_user,
    get_documents,
    get_messages,
    get_reviews,
    init_db,
    verify_user,
)
from legaliq.documents import extract_text, trim_text


st.set_page_config(page_title="LegaliQ", page_icon="⚖", layout="wide")
init_db()


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,700;1,700&display=swap');
        :root {
          --navy: #102f4d;
          --blue: #1f527c;
          --gold: #c3832b;
          --paper: #f8faf8;
          --ink: #0d2b47;
          --muted: #5f7588;
          --line: #dbe4e7;
          --mint: #4aa37b;
          --risk: #a44138;
        }
        .stApp {
          background: linear-gradient(90deg, var(--navy) 0 288px, var(--paper) 288px 100%);
          color: var(--ink);
          font-family: Inter, sans-serif;
        }
        section[data-testid="stSidebar"] {
          background: var(--navy);
          color: white;
          border-right: 0;
        }
        section[data-testid="stSidebar"] * { color: #dcecf7; }
        .block-container {
          max-width: 1500px;
          padding: 2rem 3rem 4rem 3rem;
        }
        h1, h2, h3 {
          font-family: 'Playfair Display', serif;
          color: var(--ink);
          letter-spacing: 0;
        }
        h1 { font-size: clamp(3rem, 6vw, 5.8rem); line-height: .95; margin-bottom: 1rem; }
        h2 { font-size: 2.1rem; }
        h3 { font-size: 1.45rem; }
        .brand {
          display:flex; align-items:center; gap:.8rem; margin: .3rem 0 5rem;
          font-family:'Playfair Display', serif; font-size:1.9rem; font-weight:700;
        }
        .mark {
          width:48px; height:48px; border:1px solid var(--gold); display:grid; place-items:center;
          color:var(--gold); font-family:serif; font-weight:700;
        }
        .gold { color: var(--gold); font-style: italic; }
        .eyebrow {
          color: #8aa0af; text-transform: uppercase; letter-spacing: .18em;
          font-size: .78rem; font-weight: 800;
        }
        .topbar {
          display:flex; justify-content:space-between; align-items:center;
          border-bottom:1px solid var(--line); margin:-2rem -3rem 4rem; padding: 1.1rem 3rem;
          background: rgba(255,255,255,.45);
        }
        .status { color:#2f805f; font-weight:700; }
        .panel {
          background: rgba(255,255,255,.78); border:1px solid var(--line); padding:2rem;
          box-shadow: 0 24px 80px rgba(16,47,77,.08);
        }
        .soft-panel { background:#fff; border-left:3px solid var(--gold); padding:1.25rem 1.5rem; }
        .risk-panel { background:#fff7f5; border:1px solid #f0cbc5; padding:1.5rem; }
        .notice { border-top:1px solid var(--line); margin-top:2rem; padding-top:1rem; color:#6a7f8b; }
        .history-item { border:1px solid var(--line); background:#fff; padding:1rem; margin-bottom:.75rem; }
        .small { color:var(--muted); font-size:.9rem; }
        div[data-testid="stButton"] > button {
          border-radius: 0; border:1px solid var(--gold); background:#fff; color:var(--ink);
          font-weight:700; min-height: 3rem;
        }
        div[data-testid="stButton"] > button:hover {
          border-color: var(--gold); color: var(--gold); background:#fffaf2;
        }
        .primary-button button, div[data-testid="stFormSubmitButton"] button {
          background: var(--blue) !important; color:white !important; border-color:var(--blue) !important;
        }
        textarea, input, .stSelectbox, .stTextInput { border-radius: 0 !important; }
        @media (max-width: 900px) {
          .stApp { background: var(--paper); }
          .block-container { padding: 1rem 1.1rem 3rem; }
          .topbar { margin: -1rem -1.1rem 2rem; padding: .9rem 1.1rem; }
          h1 { font-size: 3rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def slug_title(text: str, fallback: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", text)
    return " ".join(words[:7]) if words else fallback


def sidebar() -> str:
    st.sidebar.markdown("<div class='brand'><div class='mark'>⚖</div><span>Law<span style='color:#e6ac4b'>Bridge</span></span></div>", unsafe_allow_html=True)
    page = st.sidebar.radio(
        "YOUR WORKSPACE",
        ["New review", "Ask LegaliQ", "Review a document", "History"],
        label_visibility="visible",
    )
    st.sidebar.divider()
    if st.session_state.get("user"):
        st.sidebar.markdown(f"**{st.session_state.user['email']}**")
        st.sidebar.caption("Saved reviews, sessions, and documents")
        if st.sidebar.button("Sign out"):
            st.session_state.pop("user", None)
            st.rerun()
    else:
        st.sidebar.markdown("**Sign in to save**")
        st.sidebar.caption("Reviews & documents")
    st.sidebar.divider()
    st.sidebar.markdown("**Your data stays private**")
    st.sidebar.caption("Educational guidance only")
    return page


def topbar(section: str) -> tuple[str, str]:
    left = f"<span class='eyebrow'>LEGALIQ &nbsp; / &nbsp; {section.upper()}</span>"
    right = "<span class='status'>● AI assistant online</span>"
    st.markdown(f"<div class='topbar'>{left}<div>{right}</div></div>", unsafe_allow_html=True)
    cols = st.columns([1, 1, 1.2])
    language = cols[1].selectbox("Language", LANGUAGES, index=0)
    model = cols[2].radio(
        "Response depth",
        list(MODEL_OPTIONS.keys()),
        horizontal=True,
        captions=[v["description"] for v in MODEL_OPTIONS.values()],
    )
    return language, model


def login_gate() -> bool:
    if st.session_state.get("user"):
        return True

    with st.container(border=False):
        st.markdown("### Welcome back")
        st.caption("Keep your legal reviews and document history in one private place.")
        tab_signin, tab_create = st.tabs(["Sign in", "Create account"])
        with tab_signin:
            with st.form("signin"):
                email = st.text_input("Email address", placeholder="you@example.com")
                password = st.text_input("Password", type="password", placeholder="At least 8 characters")
                submitted = st.form_submit_button("Sign in →")
            if submitted:
                user = verify_user(email, password)
                if user:
                    st.session_state.user = user
                    st.success("Signed in.")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
        with tab_create:
            with st.form("create"):
                email = st.text_input("Email address", key="create_email")
                password = st.text_input("Password", type="password", key="create_password")
                submitted = st.form_submit_button("Create account")
            if submitted:
                ok, message = create_user(email, password)
                st.success(message) if ok else st.error(message)
    return False


def hero() -> None:
    st.markdown(
        """
        <div class='eyebrow'>01 &nbsp; Private legal guidance, simplified</div>
        <h1>Start with what<br><span class='gold'>happened.</span></h1>
        <p style='font-size:1.15rem;color:#526b80;max-width:680px;line-height:1.75'>
        Tell us the situation in your own words. LegaliQ will help you understand the relevant law,
        official source direction, likely remedies, risks, evidence, and practical next steps.
        </p>
        """,
        unsafe_allow_html=True,
    )


def new_review(language: str, model: str) -> None:
    hero()
    left, right = st.columns([2, 1], gap="large")
    with left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("### What do you need help with?")
        topic = st.radio(
            "Topic",
            list(TOPICS.keys()),
            horizontal=True,
            label_visibility="collapsed",
        )
        issue = st.text_area(
            "Describe your situation",
            height=210,
            placeholder="For example: I paid for a product online, but it arrived damaged and the seller stopped responding...",
        )
        st.caption("Be factual. Avoid names or sensitive numbers.")
        if st.button("Begin review →", type="primary", disabled=not issue.strip()):
            response = generate_review(topic, issue, model, language)
            title = slug_title(issue, topic)
            review_id = add_review(st.session_state.user["id"], title, topic, issue, model, language, response)
            st.session_state.active_review_id = review_id
            st.success("Review ready and saved.")
            st.markdown(response)
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        topic_data = TOPICS[topic]
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("### Preferences")
        st.write(f"**Model:** {model}")
        st.write(f"**Language:** {language}")
        st.divider()
        st.markdown("### Every review includes")
        st.write("Relevant law or article, official source direction, risks, evidence checklist, action roadmap, and draft text where suitable.")
        st.divider()
        st.markdown("### Risks to keep in view")
        for risk in topic_data.risks:
            st.write(f"- {risk}")
        st.markdown("</div>", unsafe_allow_html=True)


def ask_legaliq(language: str, model: str) -> None:
    st.markdown("<div class='eyebrow'>Conversation</div><h1>Ask <span class='gold'>LegaliQ.</span></h1>", unsafe_allow_html=True)
    reviews = get_reviews(st.session_state.user["id"])
    if not reviews:
        st.info("Start a review first so follow-up chats can attach to a saved legal map.")
        return

    labels = [f"#{r['id']} · {r['topic']} · {r['title']}" for r in reviews]
    selected = st.selectbox("Choose a saved review", labels)
    review = reviews[labels.index(selected)]
    messages = get_messages(review["id"])

    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Add what you have already done, or ask your next question")
    if question:
        add_message(review["id"], "user", question)
        answer = answer_follow_up(review["topic"], messages + [{"role": "user", "content": question}], question, model, language)
        add_message(review["id"], "assistant", answer)
        st.rerun()


def review_document(language: str, model: str) -> None:
    st.markdown("<div class='eyebrow'>Document review</div><h1>Upload a legal<br><span class='gold'>document.</span></h1>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload PDF, DOCX, or TXT", type=["pdf", "docx", "txt"])
    if uploaded:
        try:
            text = trim_text(extract_text(uploaded))
            with st.spinner("Reading document in plain language..."):
                summary = summarize_document(text, uploaded.name, model, language)
            add_document(st.session_state.user["id"], uploaded.name, summary)
            st.success("Document summary saved.")
            st.markdown(summary)
        except Exception as exc:
            st.error(str(exc))


def history() -> None:
    st.markdown("<div class='eyebrow'>Archive your workspace</div><h1>Everything you've<br><span class='gold'>looked into.</span></h1>", unsafe_allow_html=True)
    query = st.text_input("Search your history", placeholder="Search topics, articles, summaries, document names...")
    tab_reviews, tab_docs = st.tabs(["Saved reviews", "Documents"])

    with tab_reviews:
        reviews = get_reviews(st.session_state.user["id"], query)
        if not reviews:
            st.info("No saved reviews match your search.")
        for review in reviews:
            with st.expander(f"{review['topic']} · {review['title']} · {review['created_at']}"):
                st.caption(f"Model: {review['model']} · Language: {review['language']}")
                st.markdown("**Original issue**")
                st.write(review["issue"])
                st.markdown("**Saved review**")
                st.markdown(review["response"])
                st.markdown("**Conversation**")
                for message in get_messages(review["id"]):
                    st.write(f"**{message['role'].title()}:** {message['content']}")

    with tab_docs:
        docs = get_documents(st.session_state.user["id"], query)
        if not docs:
            st.info("No saved documents match your search.")
        for doc in docs:
            with st.expander(f"{doc['filename']} · {doc['created_at']}"):
                st.markdown(doc["summary"])


def main() -> None:
    inject_css()
    page = sidebar()
    language, model = topbar(page)
    if not login_gate():
        return

    if page == "New review":
        new_review(language, model)
    elif page == "Ask LegaliQ":
        ask_legaliq(language, model)
    elif page == "Review a document":
        review_document(language, model)
    else:
        history()

    st.markdown(
        "<div class='notice'><b>Educational guidance, not legal advice.</b> Laws, deadlines, and remedies depend on facts and jurisdiction. Verify cited material on official sources and consult a qualified advocate for important decisions.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
