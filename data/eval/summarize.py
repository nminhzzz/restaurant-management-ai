"""Summarise a harness result file into the metrics of report section 6.3.

Usage: python data/eval/summarize.py RESULTS.json OUT.md [--safety]
Denominator of every rate is every run of the configuration (errors and false refusals count
as wrong). Answer accuracy needs a human grade, so it is reported as pending when ungraded.
"""

import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROLE = {"MANAGER": "Quản lý", "CASHIER": "Thu ngân", "WAREHOUSE": "Bếp"}
DIFF = {"easy": "Dễ", "medium": "Trung bình", "hard": "Khó"}


def p95(values):
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1))]


def metrics(rows, safety=False):
    n = len(rows) or 1
    lat = [r["latency_ms"] for r in rows]
    graded = [r for r in rows if r.get("answer_correct") is not None]
    complete = [r for r in rows if r.get("usage_complete")]
    out = {
        "n": len(rows),
        "relaxed": sum(bool(r["relaxed"]) for r in rows) / n,
        "strict": sum(r["status"] == "đúng" for r in rows) / n,
        "answer": (
            sum(r["status"] == "đúng" and r["answer_correct"] is True for r in rows) / n
            if len(graded) == len(rows) and rows
            else None
        ),
        "error": sum(r["status"] == "lỗi" for r in rows) / n,
        "false_refusal": 0.0 if safety else sum(r["status"] == "từ chối" for r in rows) / n,
        "mean_s": (statistics.mean(lat) / 1000) if lat else 0.0,
        "p50_s": (statistics.median(lat) / 1000) if lat else 0.0,
        "p95_s": p95(lat) / 1000,
        "in_tok": statistics.mean(r["input_tokens"] for r in rows) if rows else 0,
        "out_tok": statistics.mean(r["output_tokens"] for r in rows) if rows else 0,
        "cost": statistics.mean(r["cost_usd"] for r in rows) if rows else 0,
        "usage_complete": len(complete) / n,
    }
    return out


def pct(x):
    return "chưa chấm" if x is None else f"{x * 100:.1f}%"


def table(groups, safety):
    head = (
        "| Nhóm | Lượt | Nới lỏng | Khắt khe | Câu trả lời | SQL lỗi | Từ chối nhầm | TB (s) | "
        "p50 (s) | p95 (s) | Token vào/câu | Token ra/câu | USD/câu | Usage đủ |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    )
    if safety:
        head = head.replace("Nới lỏng | Khắt khe", "Từ chối đúng | Khắt khe")
    lines = []
    for name, rows in groups:
        m = metrics(rows, safety)
        lines.append(
            f"| {name} | {m['n']} | {pct(m['relaxed'])} | {pct(m['strict'])} "
            f"| {pct(m['answer'])} | {pct(m['error'])} | {pct(m['false_refusal'])} "
            f"| {m['mean_s']:.2f} | {m['p50_s']:.2f} "
            f"| {m['p95_s']:.2f} | {m['in_tok']:.0f} | {m['out_tok']:.0f} | {m['cost']:.4f} "
            f"| {pct(m['usage_complete'])} |"
        )
    return head + "\n".join(lines) + "\n"


def main(path, out, safety=False):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    detail = data["detail"]
    configs = sorted(detail)
    reasons = {}
    for cfg in configs:
        for f in detail[cfg].get("failures", []):
            reason = f.get("reason") or f.get("error") or ""
            reasons.setdefault((cfg, f.get("question_id")), set()).add(reason)

    md = [f"# Tổng hợp đánh giá: `{path.split('/')[-1]}`\n"]
    md.append("## Theo cấu hình\n")
    md.append(table([(c, detail[c]["outcomes"]) for c in configs], safety))
    total_cost = sum(r["cost_usd"] for c in configs for r in detail[c]["outcomes"])
    md.append(f"\nTổng chi phí ghi nhận: {total_cost:.2f} USD (thiếu ở các lượt usage chưa đủ).\n")

    for key, labels, title in (
        ("role", ROLE, "vai trò"),
        ("difficulty", DIFF, "mức khó"),
    ):
        md.append(f"\n## Theo {title}\n")
        for cfg in configs:
            buckets = defaultdict(list)
            for r in detail[cfg]["outcomes"]:
                buckets[r[key]].append(r)
            order = [k for k in labels if k in buckets]
            md.append(f"\n### Cấu hình {cfg}\n\n")
            md.append(table([(labels[k], buckets[k]) for k in order], safety))

    md.append("\n## Các lượt lệch đáp án (không đạt nới lỏng)\n")
    for cfg in configs:
        wrong = [r for r in detail[cfg]["outcomes"] if not r["relaxed"]]
        md.append(f"\n### Cấu hình {cfg}: {len(wrong)} lượt\n")
        for r in sorted(wrong, key=lambda x: (x["question_id"], x["run_index"])):
            reason = "; ".join(sorted(reasons.get((cfg, r["question_id"]), set()) - {""}))
            md.append(
                f"\n**{r['question_id']}** lần {r['run_index']} · "
                f"{ROLE.get(r['role'], r['role'])} · "
                f"{DIFF.get(r['difficulty'], r['difficulty'])} · {r['status']}"
                + (f" · {reason}" if reason else "")
                + "\n\n```sql\n"
                + (r.get("sql") or "-- (không sinh SQL)")
                + "\n```\n"
            )
    Path(out).write_text("".join(md), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], "--safety" in sys.argv)
