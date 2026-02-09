"""
Run script for the Haki Sovereign AI Engine.

Usage (from project root):

  # Ask a single question
  python -m src.run -q "What are presidential qualifications?"

  # Ask from a file (one question per line)
  python -m src.run -f questions.txt

  # Run demo questions
  python -m src.run --demo

  # Rebuild vector store (first time or after adding PDFs)
  python -m src.run --rebuild

  # Output in Kiswahili or Sheng
  python -m src.run -q "Your question" -l sw
"""

import argparse
import sys
from pathlib import Path

from .haki_engine import create_engine
from .demo_questions import DEMO_QUESTIONS


def main():
    parser = argparse.ArgumentParser(
        description="Haki Sovereign AI Engine — Ask questions about official Kenyan documents."
    )
    parser.add_argument("-q", "--question", help="Ask a single question")
    parser.add_argument("-f", "--file", help="Path to file with questions (one per line)")
    parser.add_argument("--demo", action="store_true", help="Run the 10 demo acceptance questions")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild vector store from documents")
    parser.add_argument("-l", "--language", choices=["en", "sw", "sheng"], default="en", help="Output language")
    args = parser.parse_args()

    if not any([args.question, args.file, args.demo]):
        parser.print_help()
        print("\nExamples:")
        print('  python -m src.run -q "What are presidential qualifications?"')
        print("  python -m src.run -f my_questions.txt")
        print("  python -m src.run --demo")
        sys.exit(0)

    print("Initializing Haki Sovereign AI Engine...")
    engine = create_engine(force_rebuild=args.rebuild)

    questions = []
    if args.question:
        questions = [args.question.strip()]
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: File not found: {path}")
            sys.exit(1)
        questions = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    elif args.demo:
        questions = DEMO_QUESTIONS

    for q in questions:
        print("\n" + "=" * 60)
        print(f"Q: {q}")
        print("=" * 60)
        resp = engine.ask(q, language=args.language)
        out = resp.format_output()
        print("Answer:", out["answer"])
        print("Sources:", out["sources"])
        print("Supported:", out["supported"])


if __name__ == "__main__":
    main()
