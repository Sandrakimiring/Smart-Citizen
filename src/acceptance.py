"""
MVP 1 acceptance checks (no public API required).

Runs demo questions and asserts:
- supported questions return citations
- unsupported questions return exact refusal phrase

Usage:
  python -m src.acceptance --rebuild
"""

import argparse

from .config import REFUSAL_TEXT
from .demo_questions import DEMO_QUESTIONS
from .haki_engine import create_engine


def main():
    parser = argparse.ArgumentParser(description="Run MVP 1 acceptance checks.")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild vector store first")
    parser.add_argument("-l", "--language", choices=["en", "sw", "sheng"], default="en", help="Output language")
    args = parser.parse_args()

    engine = create_engine(force_rebuild=args.rebuild)

    failures = []
    for q in DEMO_QUESTIONS:
        resp = engine.ask(q, language=args.language)
        out = resp.format_output()

        # Very lightweight categorization: Tanzania question must refuse
        must_refuse = "tanzania" in q.lower()

        if must_refuse:
            if out["answer"].strip() != REFUSAL_TEXT:
                failures.append((q, "expected_refusal", out["answer"]))
            continue

        if out["answer"].strip() == REFUSAL_TEXT:
            failures.append((q, "unexpected_refusal", out["answer"]))
            continue

        if not out.get("sources") or out["sources"] == ["No matching official source found in the current knowledge base."]:
            failures.append((q, "missing_sources", out.get("sources")))

    if failures:
        print("\nFAILURES:")
        for q, kind, detail in failures:
            print(f"- {kind}: {q}\n  {detail}\n")
        raise SystemExit(1)

    print("✅ MVP 1 acceptance checks passed.")


if __name__ == "__main__":
    main()

