"""
RAG pipeline evaluation runner.

Measures top-3 recall: the fraction of questions where the correct source
document appears in the top 3 returned chunks. This is the single number
you track month-over-month as you improve the pipeline.

Usage:
    # Fill in eval_questions.csv first, then:
    python eval_runner.py

    # Target a different workspace or server:
    WORKSPACE_ID=2 API_URL=http://localhost:8001 python eval_runner.py

Output:
    eval_results_YYYY-MM-DD.csv   — per-question results
    Prints top-3 recall to stdout  — e.g. "Top-3 Recall: 60%  (12/20)"

Columns in the results CSV:
    id                  — question number
    question            — the query text
    expected_answer     — what you wrote in eval_questions.csv
    expected_source_doc — the document that should surface
    difficulty          — easy / medium / hard
    actual_answer       — first 200 chars of the top-ranked chunk
    top_3_docs          — pipe-separated list of the top-3 returned filenames
    correct_doc_in_top3 — True/False — the metric you're optimising
    answer_correct      — blank; fill in manually after reading actual_answer
    notes               — blank; add observations about failures
"""

import csv
import os
import sys
from datetime import date

import requests

# ── config ─────────────────────────────────────────────────────────────────────

API_URL      = os.environ.get("API_URL", "http://localhost:8000")
WORKSPACE_ID = int(os.environ.get("WORKSPACE_ID", "1"))
TOP_K        = 3

EVAL_CSV    = os.path.join(os.path.dirname(__file__), "eval_questions.csv")
RESULTS_CSV = os.path.join(
    os.path.dirname(__file__),
    f"eval_results_{date.today()}.csv",
)

RESULT_FIELDS = [
    "id",
    "question",
    "expected_answer",
    "expected_source_doc",
    "difficulty",
    "actual_answer",
    "top_3_docs",
    "correct_doc_in_top3",
    "answer_correct",
    "notes",
]


# ── helpers ─────────────────────────────────────────────────────────────────────

def _check_placeholders(rows: list[dict]) -> None:
    """Warn if the CSV still contains unfilled placeholder values."""
    unfilled = [r["id"] for r in rows if "<fill in" in r.get("expected_source_doc", "")]
    if unfilled:
        print(
            f"WARNING: {len(unfilled)} question(s) still have placeholder "
            f"expected_source_doc values (ids: {', '.join(unfilled)}).\n"
            "correct_doc_in_top3 will always be False for those rows.\n"
            "Fill in eval_questions.csv before treating results as meaningful.\n"
        )


def _call_search(query: str) -> dict:
    """POST to /search and return the parsed JSON body."""
    response = requests.post(
        f"{API_URL}/search",
        json={"query": query, "workspace_id": WORKSPACE_ID, "top_k": TOP_K},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


# ── main ────────────────────────────────────────────────────────────────────────

def run_eval(eval_csv_path: str = EVAL_CSV, output_csv_path: str = RESULTS_CSV) -> None:
    with open(eval_csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    _check_placeholders(rows)

    results = []
    errors  = 0

    for row in rows:
        qid = row["id"]
        print(f"  [{qid:>2}/20] {row['question'][:70]}…", end=" ", flush=True)

        try:
            data = _call_search(row["question"])
        except requests.RequestException as exc:
            print(f"ERROR — {exc}")
            errors += 1
            results.append({
                **row,
                "actual_answer":       f"REQUEST_ERROR: {exc}",
                "top_3_docs":          "",
                "correct_doc_in_top3": False,
                "answer_correct":      "",
                "notes":               "",
            })
            continue

        top_docs     = [r["source"] for r in data.get("results", [])]
        actual_answer = (data["results"][0]["content"] if data.get("results") else "")
        correct       = row["expected_source_doc"] in top_docs

        print("✓" if correct else "✗")

        results.append({
            **row,
            "actual_answer":       actual_answer[:200],
            "top_3_docs":          " | ".join(top_docs),
            "correct_doc_in_top3": correct,
            "answer_correct":      "",   # fill in manually
            "notes":               "",   # fill in manually
        })

    # ── write results ──────────────────────────────────────────────────────────
    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows(results)

    # ── summary ────────────────────────────────────────────────────────────────
    hits   = sum(1 for r in results if r["correct_doc_in_top3"] is True)
    total  = len(results)
    recall = hits / total if total else 0.0

    by_difficulty: dict[str, tuple[int, int]] = {}
    for r in results:
        diff  = r.get("difficulty", "unknown")
        h, t  = by_difficulty.get(diff, (0, 0))
        by_difficulty[diff] = (h + (1 if r["correct_doc_in_top3"] else 0), t + 1)

    print()
    print(f"Top-3 Recall: {recall:.0%}  ({hits}/{total})")
    for diff, (h, t) in sorted(by_difficulty.items()):
        print(f"  {diff:8s}: {h}/{t}")
    if errors:
        print(f"  {errors} request(s) failed — see results CSV for details")
    print(f"\nResults written to: {output_csv_path}")


if __name__ == "__main__":
    # Allow overriding paths from the command line:
    #   python eval_runner.py eval_questions.csv eval_results_custom.csv
    eval_path   = sys.argv[1] if len(sys.argv) > 1 else EVAL_CSV
    output_path = sys.argv[2] if len(sys.argv) > 2 else RESULTS_CSV
    run_eval(eval_path, output_path)
