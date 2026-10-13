---
name: ghosttrace
description: Deterministic AI trace and slop detector with academic IEEE support, LaTeX parsing, burstiness metrics, and human replacement guidance. Trigger on /ghosttrace, "remove AI traces", "check for AI tells", "humanize paper", "de-slop this draft".
---

# GhostTrace

Audit writing for subtle AI fingerprints, marketing fluff, flat burstiness cadences, and model-specific tells. Supports **General Writing**, **Technical Copy**, and **Academic/IEEE Papers**.

---

## When to Use GhostTrace

Use GhostTrace whenever you or your user needs to verify that a draft reads with natural human cadence and lacks the recognizable quirks left by LLMs.

### Available Modes:
1. **General Mode (`--mode=general`)**: For READMEs, blog posts, landing pages, emails, and scripts.
2. **Academic Mode (`--mode=academic`)**: For research papers, IEEE/ACM conference submissions, theses, and grant proposals. Whitelists technical terms (like `robust` and `leverage`) while strictly checking for unverified academic hype.

---

## Commands & Usage

```bash
# 1. Audit a raw text snippet with replacement suggestions:
python ghosttrace.py --text "In this paper, we delve into a revolutionary approach that provides seamless optimization." --suggest

# 2. Audit an IEEE LaTeX paper (.tex) and create an HTML visual heatmap:
python ghosttrace.py paper.tex --mode=academic --report --suggest

# 3. Audit a Markdown document (.md):
python ghosttrace.py README.md --suggest

# 4. Integrate into CI/CD or automation with JSON output:
python ghosttrace.py draft.txt --json
```

---

## Output Interpretation

* **Score (5/5)**:
  * `5/5 (CLEAN)`: No scored tells found.
  * `< 5/5 (NEEDS CLEANSE)`: Categorical deductions for vocabulary tells, boilerplate phrases, or monotonous cadences.
* **Burstiness ($\sigma$)**:
  * Human writing exhibits natural variance ($\sigma \ge 5.2$).
  * Monotonous AI pacing produces low variance ($\sigma < 5.0$) across sustained sentences.
* **Replacement Suggestions**:
  * Actionable human alternatives to replace robotic buzzwords without altering the intended meaning.
