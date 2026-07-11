"""Compare v1 vs v2 benchmark results."""
import json
from collections import Counter

v1 = [json.loads(l) for l in open("results/multi_domain_50/predictions.jsonl")]
v2 = [json.loads(l) for l in open("results/multi_domain_50_v2/predictions.jsonl")]

def stats(entries, label):
    n = len(entries)
    spirals = [e["spirals"] for e in entries]
    times = [e["time_s"] for e in entries]
    spiral_dist = Counter(spirals)
    insufficient = sum(1 for e in entries if "Insufficient" in e["prediction"])

    print(f"  {label}:")
    print(f"    Avg spirals: {sum(spirals)/n:.1f}")
    print(f"    Avg time:    {sum(times)/n:.0f}s ({sum(times)/n/60:.1f} min)")
    print(f"    Insufficient: {insufficient}/{n} ({insufficient/n*100:.0f}%)")
    print(f"    Spiral dist: {dict(sorted(spiral_dist.items()))}")
    print()

    # Same/different per question
    return spirals, times, insufficient

s1, t1, ins1 = stats(v1, "v1 (old)")
s2, t2, ins2 = stats(v2, "v2 (extract + prompt)")

# Per-question comparison
print("Per-question spiral comparison:")
same = diff = 0
for i, (a, b) in enumerate(zip(s1, s2)):
    if a == b:
        same += 1
    else:
        diff += 1
        print(f"  [{i}] {a} -> {b} spirals | Q: {v1[i]['question'][:50]}")
print(f"\nSame: {same}/50, Different: {diff}/50")

# Time comparison
print(f"\nTime change: +{sum(t2)/50 - sum(t1)/50:.0f}s avg ({(sum(t2)/sum(t1)-1)*100:+.0f}%)")
