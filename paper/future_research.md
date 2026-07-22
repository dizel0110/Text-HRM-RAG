# VORTEX-HRM: Future Research Strategy

Status: working notes (not published)
Last updated: 2026-07-22

---

## Known Findings (Empirically Validated)

1. **VORTEX helps structured-instruction models.** qwen2.5:7b improves +6% (68%→74%) with VORTEX. The XML protocol fits its training profile (diverse structured data).

2. **VORTEX hurts reasoning/chat models.** llama3.1:8b drops -10% (72%→62%), mistral drops -12% (68%→56%), DeepSeek-R1 drops -19% (76%→57%). Three independent confirmations.

3. **Fast/Slow Router outperforms both components.** Same-model router: 82% (+14% over naive, +8% over VORTEX). Cross-model router (llama3.1 fast / qwen2.5 VORTEX): 84% (best result).

4. **Fast-model calibration > raw accuracy.** llama3.1 (72% baseline) as fast model gives 84%, DeepSeek-R1 (76% baseline) gives 82%. llama3.1's more conservative "Insufficient evidence" triggers VORTEX fallback more often (24% vs 16%), and VORTEX rescues more of those (58% vs 38%). Net: 1 more correct answer.

5. **5 spirals sufficient.** Ablation shows plateau at 5. More spirals add latency without accuracy gain.

6. **DeepSeek-R1: best baseline, worst VORTEX.** 76% baseline is the highest on our benchmark. 57% VORTEX is the lowest. The 19% gap is the largest sensitivity.

---

## Presumed Hypotheses (Untested)

### H1: XML Protocol is the Primary Failure Mode

**Claim:** DeepSeek-R1's VORTEX failure is caused by the XML prompt format, not by reasoning traces per se.

**Why plausible:**
- DeepSeek-R1 is Qwen2.5-7B fine-tuned with RL for reasoning. The base model (qwen2.5) works with VORTEX (74%). The fine-tuning changes instruction-following behavior.
- XML requires strict output structure. Reasoning models are trained to produce free-form CoT before structured output. The two training objectives may conflict.
- If we remove XML and use plain-English prompts ("Give me a sub-question" instead of "<step>...</step>"), DeepSeek might handle VORTEX better.

**Testable prediction:** DeepSeek-R1 with plain-English VORTEX prompts should score >65% (vs 57% with XML), closing the gap toward baseline (76%).

**Experiment:** Modify VORTEX prompts to use natural language instead of XML tags. Keep the same spiral architecture. Run on T4 with DeepSeek-R1:7b.

**If confirmed:** VORTEX can be made model-agnostic by detecting model family and adapting prompts. This is a significant architectural insight.

**If refuted:** Reasoning traces fundamentally interfere with multi-hop retrieval. VORTEX is limited to structured-instruction models.

### H2: Reasoning Traces Interfere with Fact Extraction

**Claim:** DeepSeek-R1's internal CoT is not just a prompt formatting issue — the model generates reasoning tokens that VORTEX's executor misinterprets as factual content.

**Why plausible:**
- DeepSeek-R1 is trained to "think before answering." In VORTEX's executor role, this means the model produces reasoning before condensation, which pollutes the <fact> output.
- The EM score for DeepSeek-VORTEX is 32.7% (vs 2% for baseline) — the model is producing different (possibly more structured) answers, but they don't match ground truth.

**Testable prediction:** If we prepend "Do not reason step by step. Just output the answer." to VORTEX prompts for DeepSeek, accuracy should improve.

**If confirmed:** VORTEX needs a "no-reasoning" mode for CoT models. Simple system prompt adjustment.

**If refuted:** The issue is deeper — perhaps the model's internal representation of "multi-hop reasoning" conflicts with VORTEX's externalized spiral structure.

### H3: Router Gating Can Be Improved

**Claim:** The "Insufficient evidence." string-match gate is suboptimal. A trained or prompted confidence signal would be better.

**Why plausible:**
- 18% of questions get wrong answers (8% confident-wrong fast path, 10% unsolved slow path)
- Some questions that would benefit from VORTEX get confident-but-wrong answers from the fast path
- Some VORTEX fallbacks fail because the model wasn't uncertain enough to trigger the gate

**Experiment options:**
a. **Temperature-based confidence:** Run fast path with temp=0.1 and temp=0.7. High variance = uncertain → fallback.
b. **Logprob threshold:** If available, use token logprobs to measure confidence.
c. **Explicit prompt:** "Answer and rate your confidence from 0 to 1. If below 0.5, say 'Insufficient evidence.'"
d. **LLM-as-gate:** Use a small model to judge whether the fast answer is sufficient.

**Priority:** Option (c) is cheapest to test on T4. Option (a) requires multiple inference passes.

### H4: Cross-Model Routing is Underexplored

**Claim:** The 84% result (llama3.1/qwen2.5) is not a ceiling. Better model pairs exist.

**Why plausible:**
- We only tested 2 cross-model configurations. With 4 models, there are 12 possible pairs (4 fast × 3 slow).
- DeepSeek as fast model (76% baseline) with qwen2.5 VORTEX (74%) gives 82% — only 2% below best. A different slow model might help.
- qwen2.5 as fast model with itself as VORTEX (same-model) gives 82%. What about qwen2.5 fast with a different VORTEX model?

**Experiment:** Test remaining cross-model pairs on T4 (feasible: ~10-15 min each).

**Priority:** Low. The 84% ceiling is likely close. Better to focus on prompt adaptation (H1) or router improvement (H3).

### H5: Domain-Specific Performance Patterns

**Claim:** VORTEX's spiral mechanism works better for some knowledge domains than others.

**Why plausible:**
- The benchmark covers 10 domains (history, science, geography, etc.)
- Some domains require more multi-hop reasoning (e.g., "Who was born in X and discovered Y?") while others are single-hop
- VORTEX's strength is evidence chaining — domains requiring more chains should benefit more

**Experiment:** Analyze Contains accuracy per domain across all models. Identify which domains VORTEX helps/hurts.

**Priority:** Medium. This is analysis, not a new experiment. Can be done from existing predictions.jsonl files.

---

## Recommended Next Steps (Priority Order)

### Immediate (before paper submission)
1. **Write Future Work section** — 1 paragraph hinting at H1 (prompt adaptation) and H3 (router improvement). Don't overcommit.
2. **Polish paper** — fix any formatting issues, check page count.

### Short-term (next experiment, if time permits)
3. **Test H1: DeepSeek + plain-English prompts** — 1 experiment, ~50 min on T4. High scientific value. If it works, it's a major finding: VORTEX can be made model-agnostic.

### Medium-term (future research)
4. **Test H3: Better router gating** — requires more engineering but could push accuracy above 85%.
5. **Test H5: Domain analysis** — zero-cost analysis from existing data.
6. **HotpotQA evaluation** — scaling to established benchmark. Requires corpus preparation.

### Long-term (separate paper)
7. **Model-adaptive VORTEX** — detect model family, select prompt template automatically.
8. **Cross-model router optimization** — systematic search over model pairs + gating strategies.
9. **VORTEX for non-QA tasks** — document summarization, fact verification.

---

## Open Questions

- **Is VORTEX fundamentally limited to structured-instruction models?** H1 test will answer this.
- **Can the router push above 85%?** H3 is the path.
- **Does VORTEX generalize beyond our 50-question benchmark?** Need HotpotQA or similar.
- **What is the theoretical upper bound?** If baseline is 76% and VORTEX adds ~8% ceiling, is 84% close to max? Or can prompt engineering push further?

---

## Experiment Log Summary

| Run | Model | Type | Contains | Key Finding |
|---|---|---|---|---|
| 1 | qwen2.5:7b | VORTEX | 74% | Best VORTEX, helps +6% |
| 2 | qwen2.5:7b | Baseline | 68% | Reference baseline |
| 6 | mistral | VORTEX | 56% | Weakest model, -12% |
| 8 | llama3.1:8b | VORTEX | 62% | Chat model, -10% |
| 11 | llama3.1→qwen2.5 | Router | 84% | Best result (cross-model) |
| 12 | DeepSeek-R1 | Baseline | 76% | Best baseline |
| 13 | DeepSeek-R1 | VORTEX | 57% | Worst VORTEX, -19% |
| 14 | DeepSeek→qwen2.5 | Router | 82% | Calibration > accuracy |
