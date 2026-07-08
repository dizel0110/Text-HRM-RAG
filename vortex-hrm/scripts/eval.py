"""
VORTEX evaluation script.
Computes EM, F1, Contains (LLM-as-judge optional), and cost metrics.

Usage:
    python scripts/eval.py --predictions results/predictions.jsonl
    python scripts/eval.py --predictions results/predictions.jsonl --llm-judge --config configs/openai.yaml
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from utils.metrics import compute_exact_match, compute_f1_score


def load_predictions(path: str) -> list[dict]:
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def normalize_answer(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()


def compute_contains(prediction: str, ground_truth: str) -> float:
    pred_norm = normalize_answer(prediction)
    gt_norm = normalize_answer(ground_truth)
    return 1.0 if gt_norm in pred_norm else 0.0


class LLMJudge:
    def __init__(self, config_path: Optional[str] = None):
        self.available = False
        if config_path:
            try:
                from core.config import VORTEXConfig
                from core.llm import backend_from_config
                cfg = VORTEXConfig.from_yaml(config_path)
                self.backend = backend_from_config(cfg.llm)
                self.model = cfg.llm.model
                self.available = True
            except Exception:
                pass

    def judge(self, question: str, prediction: str, ground_truth: str) -> float:
        if not self.available:
            return 0.0
        prompt = f"""Question: {question}
Predicted answer: {prediction}
Ground truth: {ground_truth}

Does the predicted answer contain the ground truth?
Reply with only YES or NO."""
        resp = self.backend.chat_completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10,
        )
        content = resp["choices"][0]["message"]["content"].strip().upper()
        return 1.0 if content.startswith("YES") else 0.0


def main():
    parser = argparse.ArgumentParser(description="VORTEX evaluation")
    parser.add_argument("--predictions", required=True, help="Path to predictions JSONL")
    parser.add_argument("--llm-judge", action="store_true", help="Use LLM-as-judge for contains")
    parser.add_argument("--config", default=None, help="Config for LLM judge backend")
    args = parser.parse_args()

    entries = load_predictions(args.predictions)
    if not entries:
        print("No predictions found.")
        return

    judge = LLMJudge(args.config) if args.llm_judge else LLMJudge()

    em_scores = []
    f1_scores = []
    cont_scores = []

    for entry in entries:
        pred = entry.get("prediction", "")
        gt = entry.get("ground_truth", "")
        question = entry.get("question", "")

        em = compute_exact_match(pred, gt)
        f1 = compute_f1_score(pred, gt)
        cont = compute_contains(pred, gt)

        if args.llm_judge and judge.available:
            llm_cont = judge.judge(question, pred, gt)
            cont = max(cont, llm_cont)

        em_scores.append(em)
        f1_scores.append(f1)
        cont_scores.append(cont)

    total = len(entries)
    print(f"\n{'='*50}")
    print(f"VORTEX Evaluation — {total} questions")
    print(f"{'='*50}")
    print(f"  EM (Exact Match):         {sum(em_scores)/total*100:.1f}%")
    print(f"  F1 (Token F1):            {sum(f1_scores)/total*100:.1f}%")
    print(f"  Contains (Ground in Pred): {sum(cont_scores)/total*100:.1f}%")

    if judge.available:
        print(f"  (LLM judge: {judge.model})")


if __name__ == "__main__":
    main()
