import re
import string
from collections import Counter


def normalize_answer(text: str) -> str:
    text = text.lower()
    text = re.sub(r"<[^>]+>", " ", text)  # strip XML tags
    text = re.sub(r"(no evidence found for this sub-question|insufficient evidence)", "", text)
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def compute_exact_match(prediction: str, ground_truth: str) -> float:
    return float(normalize_answer(prediction) == normalize_answer(ground_truth))


def compute_f1_score(prediction: str, ground_truth: str) -> float:
    pred_tokens = normalize_answer(prediction).split()
    gt_tokens = normalize_answer(ground_truth).split()

    if not pred_tokens or not gt_tokens:
        return 0.0

    pred_counter = Counter(pred_tokens)
    gt_counter = Counter(gt_tokens)

    common = pred_counter & gt_counter
    num_same = sum(common.values())

    precision = num_same / len(pred_tokens) if pred_tokens else 0.0
    recall = num_same / len(gt_tokens) if gt_tokens else 0.0

    if precision + recall == 0.0:
        return 0.0

    f1 = 2 * precision * recall / (precision + recall)
    return f1
