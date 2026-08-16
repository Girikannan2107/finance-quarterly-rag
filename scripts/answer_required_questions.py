import sys
import time
from pathlib import Path

# Reconfigure stdout/stderr to support Unicode characters (e.g. Rupee symbol) on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag_pipeline import FinanceRAG


def main() -> None:

    print("Initializing FinanceRAG pipeline...")
    rag = FinanceRAG()

    questions_file = ROOT / "tests" / "required_questions.txt"
    if not questions_file.exists():
        print(f"Error: {questions_file} not found.")
        sys.exit(1)

    questions = []
    with open(questions_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Strip index like "1. "
            if line[0].isdigit() and ". " in line:
                line = line.split(". ", 1)[1]
            # Strip tag like "[TRAP — must refuse]"
            if " [TRAP" in line:
                line = line.split(" [TRAP")[0].strip()
            # Strip trailing bracket traps if any
            line = line.replace("[TRAP — must refuse]", "").strip()
            questions.append(line)

    print(f"Loaded {len(questions)} questions from {questions_file.name}:")
    for i, q in enumerate(questions, start=1):
        print(f"{i}. {q}")

    print("\nAnswering questions using FinanceRAG...")
    results = []
    for i, q in enumerate(questions, start=1):
        print(f"\n--- Question {i}: {q} ---")
        try:
            res = rag.ask(q)
            print("Answer:")
            print(res["answer"])
            print("Sources:")
            for s in res["sources"]:
                print(f" - {s['file']} (Page {s['page']}, {s['quarter']})")
            results.append((i, q, res))
        except Exception as exc:
            print(f"Error answering question: {exc}")
            results.append((i, q, {"answer": f"ERROR: {exc}", "sources": []}))
        
        # Avoid hitting Groq API rate limits (TPM)
        if i < len(questions):
            time.sleep(6)


    # Write to a report file
    report_file = ROOT / "data" / "required_questions_answers.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        for i, q, res in results:
            f.write(f"Question {i}: {q}\n")
            f.write(f"Answer: {res['answer']}\n")
            f.write("Sources:\n")
            for s in res.get("sources", []):
                f.write(f" - {s['file']} (Page {s['page']}, {s['quarter']})\n")
            f.write("\n" + "=" * 80 + "\n\n")

    print(f"\nSaved all answers to: {report_file}")


if __name__ == "__main__":
    main()
