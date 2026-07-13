"""Generate VORTEX architecture diagram for paper and poster.
Run with: python figs/architecture.py
Requires: matplotlib, numpy
Output: figs/architecture.png (for poster), figs/architecture.pdf (for paper)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig, ax = plt.subplots(1, 1, figsize=(8, 4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 5)
ax.axis("off")

# Colors
PURPLE = "#667eea"
BLUE = "#4a8af4"
GREEN = "#4caf50"
DARK = "#1a1a2e"
GRAY = "#888888"

# Planner box (left)
planner = mpatches.FancyBboxPatch(
    (0.5, 1.5), 3.5, 2.5, boxstyle="round,pad=0.15",
    facecolor=DARK, edgecolor=PURPLE, linewidth=2.5
)
ax.add_patch(planner)
ax.text(2.25, 3.5, "Gravitational Core", fontsize=11, fontweight="bold",
        color=PURPLE, ha="center", va="center")
ax.text(2.25, 3.0, "(Planner)", fontsize=9, color=BLUE, ha="center", va="center")
ax.text(2.25, 2.4, "0 facts in weights", fontsize=8, color=GRAY, ha="center", va="center")
ax.text(2.25, 2.0, "Pure structural router", fontsize=8, color=GRAY, ha="center", va="center")

# Executor box (right)
executor = mpatches.FancyBboxPatch(
    (6.0, 1.5), 3.5, 2.5, boxstyle="round,pad=0.15",
    facecolor=DARK, edgecolor=PURPLE, linewidth=2.5
)
ax.add_patch(executor)
ax.text(7.75, 3.5, "Centrifugal Ingestor", fontsize=11, fontweight="bold",
        color=PURPLE, ha="center", va="center")
ax.text(7.75, 3.0, "(Executor)", fontsize=9, color=BLUE, ha="center", va="center")
ax.text(7.75, 2.4, "keyword $\rightarrow$ chunk $\rightarrow$ condense", fontsize=8, color=GRAY, ha="center", va="center")
ax.text(7.75, 2.0, "Chained retrieval pipeline", fontsize=8, color=GRAY, ha="center", va="center")

# Arrows
ax.annotate("", xy=(5.8, 2.75), xytext=(4.0, 2.75),
            arrowprops=dict(arrowstyle="->", color=BLUE, lw=2.5))
ax.text(4.9, 2.85, "<step>", fontsize=8, color=BLUE, ha="center", va="center")

ax.annotate("", xy=(4.0, 2.0), xytext=(5.8, 2.0),
            arrowprops=dict(arrowstyle="->", color=GREEN, lw=2.5))
ax.text(4.9, 1.9, "<fact>", fontsize=8, color=GREEN, ha="center", va="center")

# Legend
ax.text(2.25, 0.8, "Spiral cycle", fontsize=10, color=BLUE, ha="center",
        fontweight="bold")
ax.text(2.25, 0.4, "Planner $\rightarrow$ step $\rightarrow$ Executor $\rightarrow$ fact $\rightarrow$ ... $\rightarrow$ convergence",
        fontsize=8, color=GRAY, ha="center")

plt.tight_layout(pad=0.5)
plt.savefig("figs/architecture.png", dpi=200, bbox_inches="tight",
            facecolor="#0f0f1a")
plt.savefig("figs/architecture.pdf", bbox_inches="tight",
            facecolor="#0f0f1a")
print("Saved figs/architecture.png and figs/architecture.pdf")
