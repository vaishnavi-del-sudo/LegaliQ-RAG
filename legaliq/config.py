from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
DB_PATH = DATA_DIR / "legaliq.sqlite3"
KNOWLEDGE_BASE_DIR = APP_DIR / "knowledge_base"
VECTOR_DB_DIR = DATA_DIR / "chroma"

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_COLLECTION_NAME = "legaliq_legal_documents"

TOP_K_RESULTS = 5


MODEL_OPTIONS = {
    "Gemini 3.8 Flash": {
        "model_id": "gemini-3.8-flash",
        "description": "Fast and capable reasoning model",
    },
    "Gemini 3.1 Pro": {
        "model_id": "gemini-3.1-pro-preview",
        "description": "Deeper reasoning",
    },
}


LANGUAGES = [
    "English",
    "Hindi",
    "Tamil",
    "Telugu",
    "Kannada",
    "Malayalam",
    "Bengali",
    "Marathi",
    "Gujarati",
    "Punjabi",
]


@dataclass(frozen=True)
class Topic:
    name: str
    icon: str
    article: str
    source: str
    risks: tuple[str, ...]
    evidence: tuple[str, ...]
    roadmap: tuple[str, ...]


TOPICS = {
    "FIR & complaints": Topic(
        name="FIR & complaints",
        icon="⚖",
        article="Bharatiya Nagarik Suraksha Sanhita, 2023 and Bharatiya Nyaya Sanhita, 2023",
        source="India Code and local police complaint process",
        risks=(
            "Delay can make evidence harder to preserve or verify.",
            "Incorrect facts in a complaint can weaken the matter.",
            "Some disputes are civil in nature and may not become an FIR without cognizable offence facts.",
        ),
        evidence=(
            "Dates, places, names, phone numbers, and screenshots",
            "Any medical, financial, or property records",
            "Prior messages, notices, acknowledgements, or police diary number",
        ),
        roadmap=(
            "Write a factual chronology with dates and supporting material.",
            "Approach the police station or online police portal for your state.",
            "If refused, escalate to senior police officers or seek legal help for court-directed registration.",
        ),
    ),
    "Cybercrime & fraud": Topic(
        name="Cybercrime & fraud",
        icon="↯",
        article="Information Technology Act, 2000, Bharatiya Nyaya Sanhita, 2023",
        source="India Code, National Cyber Crime Portal, 1930 helpline",
        risks=(
            "Recovery becomes harder as funds move through multiple accounts.",
            "Shared Aadhaar, PAN, OTP, or login details can be reused for further fraud.",
            "Deleting chats or resetting devices may destroy useful evidence.",
        ),
        evidence=(
            "Transaction IDs, bank statement, UPI handles, and merchant details",
            "Screenshots, URLs, phone numbers, emails, and chat history",
            "Cybercrime acknowledgement number and bank complaint number",
        ),
        roadmap=(
            "Call 1930 and notify your bank's fraud team immediately.",
            "Preserve original messages and device data without editing.",
            "File the full complaint at cybercrime.gov.in and with the local Cyber Cell.",
        ),
    ),
    "Consumer rights": Topic(
        name="Consumer rights",
        icon="◇",
        article="Consumer Protection Act, 2019 and Consumer Protection (E-Commerce) Rules, 2020",
        source="India Code, National Consumer Helpline, e-Daakhil",
        risks=(
            "Return, warranty, or limitation windows may close while the dispute is delayed.",
            "Terms may contain arbitration, jurisdiction, or refund conditions.",
            "Recovery may be difficult if the seller has no traceable address or valid registration.",
        ),
        evidence=(
            "Invoice, order confirmation, warranty card, and payment proof",
            "Photos, videos, delivery proof, and defect evidence",
            "Written support refusal, complaint ticket numbers, and seller messages",
        ),
        roadmap=(
            "Send a written demand for refund, replacement, or service correction.",
            "Register the grievance with National Consumer Helpline at 1915.",
            "Consider e-Daakhil if the issue remains unresolved.",
        ),
    ),
    "Workplace issues": Topic(
        name="Workplace issues",
        icon="▣",
        article="Industrial Disputes Act, 1947, Shops and Establishments laws, POSH Act, 2013",
        source="India Code, state labour department, internal committee records",
        risks=(
            "Employment remedies can depend on worker category and state-specific law.",
            "Internal complaint deadlines and limitation periods may apply.",
            "Retaliation risk should be documented and handled carefully.",
        ),
        evidence=(
            "Offer letter, salary slips, attendance records, and HR policies",
            "Emails, chats, warning letters, appraisal records, and resignation material",
            "Witness names and internal complaint acknowledgements",
        ),
        roadmap=(
            "Organize employment records and create a factual timeline.",
            "Use the internal HR, grievance, or POSH process where applicable.",
            "Escalate to the labour department, legal notice, or appropriate forum if unresolved.",
        ),
    ),
    "Family & maintenance": Topic(
        name="Family & maintenance",
        icon="○",
        article="Code of Criminal Procedure legacy principles, Bharatiya Nagarik Suraksha Sanhita, family laws",
        source="India Code and Family Court process",
        risks=(
            "Personal law, marriage status, child custody, and residence facts can change remedies.",
            "Informal settlements may be hard to enforce without written terms.",
            "Safety concerns should be addressed before mediation or confrontation.",
        ),
        evidence=(
            "Marriage, birth, residence, income, and expense records",
            "Messages, prior complaints, medical records, and bank statements",
            "School, rent, household, and child-care expense proof",
        ),
        roadmap=(
            "Prepare a concise timeline and list immediate safety or support needs.",
            "Consult a family lawyer or legal aid service for forum-specific options.",
            "Use mediation, protection, maintenance, or custody proceedings as facts require.",
        ),
    ),
    "Broad legal query": Topic(
        name="Broad legal query",
        icon="§",
        article="Relevant Indian statutes and official legal sources",
        source="India Code and government portals",
        risks=(
            "The correct remedy may change by state, limitation period, and document facts.",
            "AI summaries can miss facts that a qualified advocate would treat as decisive.",
            "Acting without verifying law and procedure can harm your position.",
        ),
        evidence=(
            "All documents, notices, receipts, messages, and government acknowledgements",
            "A date-wise timeline of what happened and what has already been tried",
            "Names of authorities, case numbers, and forum records if any",
        ),
        roadmap=(
            "Identify the legal category and the immediate deadline or risk.",
            "Collect official records and preserve evidence before contacting the other side.",
            "Verify the remedy with official portals or a qualified advocate.",
        ),
    ),
}
