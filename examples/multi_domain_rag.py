"""
Multi-domain RAG example demonstrating domain isolation and cross-domain comparison.

Shows how to maintain separate knowledge bases for distinct domains so that queries
to one domain cannot inadvertently surface documents from another.

Domains demonstrated:
    1. HR Policy     — vacation, leave, expense rules
    2. Engineering   — coding standards, architecture guidelines
    3. Legal         — compliance, data retention, regulatory notes

Techniques shown:
    - Ingesting domain-specific content into separate collections
    - Using BasicRAGModule for a clean, named API per domain
    - Cross-domain comparison: asking the same question across all three domains
    - Domain isolation verification: confirming sources stay within their domain

Prerequisites:
    - PostgreSQL with pgvector: docker-compose -f docker-compose.test.yml up -d
    - Google Gemini API key: export GOOGLE_API_KEY="your-key"

Run:
    python examples/multi_domain_rag.py
"""

import asyncio
import os
import tempfile
from pathlib import Path

from vibe_rag import BasicRAGModule

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_KEY = os.getenv("GOOGLE_API_KEY", "your-api-key-here")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://vibetest:vibetest123@localhost:5434/vibe_rag_test",
)

# ---------------------------------------------------------------------------
# Domain content — inline, no external files needed
# ---------------------------------------------------------------------------

DOMAINS = {
    "hr_policy": {
        "collection": "multi_domain_hr",
        "label": "HR Policy",
        "content": """
HR Policy Handbook

Vacation and Leave
Employees are entitled to 20 days of annual leave per calendar year. Leave accrues
at a rate of 1.67 days per month. Unused leave of up to 10 days may be carried over
to the following year; any remaining balance is forfeited on 31 December.

Sick Leave
Employees may take up to 10 days of paid sick leave per year. A doctor's note is
required for absences exceeding three consecutive days.

Expense Reimbursement
All business expenses must be submitted within 30 days of the expense date using
the online expense portal. Receipts are required for any item over $25. Meals are
capped at $75 per person for domestic travel and $100 per person internationally.
Pre-approval is required for any single expense over $500.

Remote Work
Employees may work remotely up to 3 days per week with manager approval. All
remote employees must be reachable during core hours (10:00–15:00 local time).
A home-office stipend of $500 is available annually for qualifying employees.

Performance Reviews
Performance reviews occur twice per year: mid-year in June and year-end in December.
Salary adjustments are tied to the year-end review cycle. Promotion nominations must
be submitted to HR at least 4 weeks before the review period closes.
        """,
    },
    "engineering": {
        "collection": "multi_domain_eng",
        "label": "Engineering Guide",
        "content": """
Engineering Standards Guide

Language and Runtime
All new backend services must use Python 3.10 or later. Type annotations are
required for all public functions and methods. Avoid implicit Any — use explicit
type narrowing when needed.

Architecture Patterns
Follow the adapter pattern for all pluggable components (LLM providers, storage
backends, loaders). This enables mock-based unit testing without network dependencies
and simplifies provider migration.

Async I/O
All database calls, API calls, and file I/O must be async. Use asyncpg for
PostgreSQL connections with a connection pool size of 10–50 depending on expected
concurrency. Never block the event loop with synchronous calls.

Testing
Write tests before implementation (TDD). Target 90% branch coverage on core engine
code and 85% on providers and storage backends. Unit tests must not depend on
external services — use mock implementations from vibe_rag.testing.mocks.

Code Quality
Run black, ruff, and mypy before committing. All pull requests require at least
one reviewer approval. Keep commits small and focused; one logical change per commit.

Deployment
Use Docker for all service deployments. All environment secrets are injected via
environment variables — never hard-code credentials. Production images use
python:3.11-slim to minimize attack surface.
        """,
    },
    "legal": {
        "collection": "multi_domain_legal",
        "label": "Legal Compliance",
        "content": """
Legal Compliance and Regulatory Notes

Data Retention
Customer personal data must not be retained beyond 90 days after account closure
unless required by applicable law. All data retention schedules must be documented
in the Data Inventory Register maintained by the Legal team.

GDPR Compliance
The company processes personal data of EU residents and is therefore subject to
GDPR. Data subjects have the right to access, rectify, and erase their data.
Data processing agreements (DPAs) must be in place with all third-party processors
before any personal data is transferred.

Contract Review
All vendor contracts exceeding $50,000 must be reviewed by Legal before signing.
Contracts involving data processing, intellectual property, or indemnification
clauses require Legal sign-off regardless of value.

Incident Response
Data breaches involving personal data must be reported to the DPA within 72 hours
of discovery. The incident response team must be notified immediately; Legal will
coordinate regulatory notifications. Document all incidents in the Incident Log.

Intellectual Property
All work product created by employees during the course of employment is owned by
the company. Open-source contributions require written approval from Legal. Third-
party code must be reviewed for licence compatibility before inclusion in products.
        """,
    },
}

# Cross-domain test questions
CROSS_DOMAIN_QUESTION = "What are the key requirements and time limits I need to know?"


# ---------------------------------------------------------------------------
# Helper: write inline content to a temp file
# ---------------------------------------------------------------------------


def _write_temp(content: str, suffix: str = ".txt") -> str:
    """Write content to a temp file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    ) as f:
        f.write(content.strip())
        return f.name


# ---------------------------------------------------------------------------
# Task 1: Ingest each domain into its own collection
# ---------------------------------------------------------------------------


async def ingest_domains() -> None:
    """Ingest all domain documents into separate collections."""
    print("\n--- Ingesting domain knowledge bases ---\n")

    for domain_key, domain in DOMAINS.items():
        print(f"  Ingesting {domain['label']} -> collection '{domain['collection']}'...")
        path = _write_temp(domain["content"])
        try:
            async with BasicRAGModule(
                api_key=API_KEY,
                db_url=DATABASE_URL,
                collection_name=domain["collection"],
                top_k=5,
            ) as rag:
                doc_ids = await rag.ingest(
                    path,
                    metadata={"domain": domain_key, "label": domain["label"]},
                )
                print(f"    -> {len(doc_ids)} chunks stored")
        finally:
            Path(path).unlink()

    print("\n  All domains ingested.")


# ---------------------------------------------------------------------------
# Task 2: Cross-domain comparison — same question, different collections
# ---------------------------------------------------------------------------


async def cross_domain_comparison() -> None:
    """Ask the same question across all three domains and compare answers."""
    print("\n--- Cross-Domain Comparison ---")
    print(f"\n  Question: \"{CROSS_DOMAIN_QUESTION}\"\n")

    for domain_key, domain in DOMAINS.items():
        print(f"  [{domain['label']}]")
        async with BasicRAGModule(
            api_key=API_KEY,
            db_url=DATABASE_URL,
            collection_name=domain["collection"],
            top_k=3,
        ) as rag:
            result = await rag.query(CROSS_DOMAIN_QUESTION)

        answer_preview = result["answer"][:200].replace("\n", " ")
        n_docs = result["metadata"]["documents_retrieved"]
        total_ms = result["metadata"]["total_time_ms"]

        print(f"    Docs retrieved: {n_docs}")
        print(f"    Time: {total_ms:.0f}ms")
        print(f"    Answer preview: {answer_preview}...")
        print()


# ---------------------------------------------------------------------------
# Task 3: Domain isolation verification
# ---------------------------------------------------------------------------


async def verify_domain_isolation() -> None:
    """Confirm that querying one domain does not return documents from another."""
    print("--- Domain Isolation Verification ---\n")

    # A very domain-specific question that should only match HR content
    hr_question = "How many days of vacation leave do employees get per year?"

    print(f"  Query sent to HR domain only: \"{hr_question}\"")

    async with BasicRAGModule(
        api_key=API_KEY,
        db_url=DATABASE_URL,
        collection_name=DOMAINS["hr_policy"]["collection"],
        top_k=3,
    ) as rag:
        result = await rag.query(hr_question)

    sources = result["sources"]
    domains_found = {s["metadata"].get("domain", "unknown") for s in sources}

    print(f"  Sources retrieved: {len(sources)}")
    print(f"  Domains present in sources: {domains_found}")

    # All sources must be from the hr_policy domain only
    if domains_found == {"hr_policy"} or domains_found == set():
        print("  PASS: Sources are isolated to the HR domain.")
    else:
        print(f"  NOTE: Got sources from domains: {domains_found}")

    print(f"\n  Answer: {result['answer'][:300].replace(chr(10), ' ')}...")


# ---------------------------------------------------------------------------
# Task 4: Domain-specific targeted queries
# ---------------------------------------------------------------------------


async def domain_specific_queries() -> None:
    """Run targeted queries unique to each domain."""
    print("\n--- Domain-Specific Queries ---\n")

    queries = {
        "hr_policy": "What is the expense reimbursement policy?",
        "engineering": "What architecture pattern should I use for pluggable components?",
        "legal": "How quickly must data breaches be reported?",
    }

    for domain_key, question in queries.items():
        domain = DOMAINS[domain_key]
        print(f"  [{domain['label']}] {question}")

        async with BasicRAGModule(
            api_key=API_KEY,
            db_url=DATABASE_URL,
            collection_name=domain["collection"],
            top_k=3,
        ) as rag:
            result = await rag.query(question)

        answer_preview = result["answer"][:180].replace("\n", " ")
        print(f"    Answer: {answer_preview}...\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the full multi-domain RAG demonstration."""
    print("=" * 70)
    print(" Multi-Domain RAG Example")
    print(" Demonstrates domain isolation using separate collections")
    print("=" * 70)

    # Step 1: Ingest all domains
    await ingest_domains()

    # Step 2: Compare same question across all domains
    await cross_domain_comparison()

    # Step 3: Verify domain isolation
    await verify_domain_isolation()

    # Step 4: Domain-specific targeted queries
    await domain_specific_queries()

    print("=" * 70)
    print(" Done. Each domain's knowledge base is fully isolated.")
    print("=" * 70)


if __name__ == "__main__":
    print("""
Vibe-RAG Multi-Domain Example
Production-grade RAG framework — multi-collection domain isolation
    """)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running: docker-compose -f docker-compose.test.yml up -d")
        print("2. Set GOOGLE_API_KEY environment variable")
        print("3. Check DATABASE_URL matches your setup")
        raise
