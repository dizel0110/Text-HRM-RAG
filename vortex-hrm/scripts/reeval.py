"""
Re-evaluate old predictions after answer extractor improvements.
Shows BEFORE (old XML-raw) vs AFTER (with extract_answer) metrics.

Usage:
    python scripts/reeval.py --predictions results/multi_domain_50/predictions.jsonl
"""

import argparse
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from utils.metrics import compute_exact_match, compute_f1_score, normalize_answer
from orchestrator import VortexEngine


def load_predictions(path: str) -> list[dict]:
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def compute_contains(prediction: str, ground_truth: str) -> float:
    pred_norm = normalize_answer(prediction)
    gt_norm = normalize_answer(ground_truth)
    return 1.0 if gt_norm in pred_norm else 0.0


def main():
    parser = argparse.ArgumentParser(description="Re-evaluate old predictions")
    parser.add_argument("--predictions", required=True, help="Path to predictions JSONL")
    args = parser.parse_args()

    entries = load_predictions(args.predictions)
    if not entries:
        print("No predictions found.")
        return

    em_before = []
    f1_before = []
    cont_before = []

    em_after = []
    f1_after = []
    cont_after = []

    total_spirals = 0
    total_time = 0.0
    insufficient = 0
    spiral_dist = {}

    for entry in entries:
        raw_pred = entry.get("prediction", "")
        gt = entry.get("ground_truth", "")
        clean_pred = VortexEngine.extract_answer(raw_pred)

        spirals = entry.get("spirals", 0)
        total_spirals += spirals
        total_time += entry.get("time_s", 0)
        spiral_dist[spirals] = spiral_dist.get(spirals, 0) + 1

        if raw_pred.strip() == "Insufficient evidence.":
            insufficient += 1

        em_before.append(compute_exact_match(raw_pred, gt))
        f1_before.append(compute_f1_score(raw_pred, gt))
        cont_before.append(compute_contains(raw_pred, gt))

        em_after.append(compute_exact_match(clean_pred, gt))
        f1_after.append(compute_f1_score(clean_pred, gt))
        cont_after.append(compute_contains(clean_pred, gt))

    n = len(entries)
    avg_spirals = total_spirals / n if n else 0
    avg_time = total_time / n if n else 0

    print("=" * 56)
    print("VORTEX Re-Evaluation: BEFORE vs AFTER Answer Extractor")
    print("=" * 56)
    print(f"  Questions: {n}")
    print(f"  Insufficient: {insufficient}/{n} ({insufficient/n*100:.0f}%)")
    print(f"  Avg spirals: {avg_spirals:.1f}")
    print(f"  Avg time:    {avg_time:.0f}s ({avg_time/60:.1f} min)")
    print()

    print(f"  {'Metric':<18} {'BEFORE':<14} {'AFTER':<14} {'Δ':<10}")
    print(f"  {'-'*18} {'-'*14} {'-'*14} {'-'*10}")
    print(f"  {'Contains':<18} {sum(cont_before)/n*100:>6.1f}%{'':>6} {sum(cont_after)/n*100:>6.1f}%{'':>6} {sum(cont_after)/n*100 - sum(cont_before)/n*100:>+5.1f}%")
    print(f"  {'F1':<18} {sum(f1_before)/n*100:>6.1f}%{'':>6} {sum(f1_after)/n*100:>6.1f}%{'':>6} {sum(f1_after)/n*100 - sum(f1_before)/n*100:>+5.1f}%")
    print(f"  {'EM':<18} {sum(em_before)/n*100:>6.1f}%{'':>6} {sum(em_after)/n*100:>6.1f}%{'':>6} {sum(em_after)/n*100 - sum(em_before)/n*100:>+5.1f}%")
    print()

    print("  Spiral distribution:")
    for s in sorted(spiral_dist.keys()):
        bar = "█" * spiral_dist[s]
        print(f"    {s}: {spiral_dist[s]:>2} ({spiral_dist[s]/n*100:.0f}%) {bar}")

    print()
    print("  Spiral distribution (cumulative >0):")
    nonzero = sum(v for k, v in spiral_dist.items() if k > 0)
    for s in sorted(spiral_dist.keys()):
        if s > 0:
            print(f"    {s}: {spiral_dist[s]:>2} ({spiral_dist[s]/nonzero*100:.0f}% of non-zero)")


if __name__ == "__main__":
    main()
