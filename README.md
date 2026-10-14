# GhostTrace

> **Deterministic AI Trace & Slop Detection Engine**  
> Uncover subtle AI writing fingerprints, promotional filler, flat burstiness cadences, and model-specific tells across General, Academic (IEEE/Research), and Technical documents.

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3](https://img.shields.io/badge/Python-3.8%2B-green.svg)
![Zero Dependencies](https://img.shields.io/badge/Dependencies-Standard%20Library-brightgreen.svg)

---

## Why GhostTrace?

Traditional AI detectors (e.g., Turnitin, GPTZero) are **black boxes** that spit out opaque probabilities like *"73% AI Generated"* without explaining why. They frequently create **false positives** on technical papers, penalizing researchers for using terms like `robust optimization` or `leveraging a dataset`.

**GhostTrace** is completely transparent:

1. **Explainable:** Flags exact syntax patterns, vocabulary tells, and rhythm anomalies.
2. **Domain-Aware:** Includes an `--mode=academic` setting tailored for IEEE, ACM, and Springer papers.
3. **LaTeX Native:** Strips math environments, citations, and tags without breaking.
4. **Statistical Burstiness:** Detects the flat, monotonous sentence rhythm characteristic of LLMs.
5. **Interactive Guidance:** Proposes human synonyms and generates an HTML visual heatmap.
6. **100% Offline & Private:** Zero cloud API dependencies; your unpublished research never leaves your machine.

---

## Quick Start

GhostTrace uses Python 3 and its standard library. No packages or API keys are required.

```bash
# Clone the repository
git clone https://github.com/SridharShyam/GhostTrace.git
cd GhostTrace

# Audit a short draft with replacement suggestions
python ghosttrace.py --text "In this paper, we delve into a revolutionary approach that provides seamless optimization." --suggest

# Audit an IEEE LaTeX paper and generate a visual heatmap report
python ghosttrace.py paper.tex --mode=academic --report --suggest

# Audit a Markdown or plain text document
python ghosttrace.py README.md --suggest
```

---

## Core Features & Modes

### 1. Academic Mode (`--mode=academic`)

Tuned specifically for scientific papers, theses, and grant proposals:

* **Whitelists Technical Vocabulary:** Legitimate terminology like `robust control`, `leveraging`, or `empirical framework` will not be penalized.
* **Flags Promotional Hype:** Traps subjective superlatives (*game-changing*, *revolutionary breakthrough*, *unprecedented accuracy*).
* **Catches LLM Literature Boilerplate:** Flags unverified claims like *"extensive experiments have demonstrated"* or *"with the rapid development of..."*.

### 2. LaTeX Parser (`.tex`)

Native support for LaTeX papers. Automatically filters:

* Citations (`\cite{...}`, `\citep{...}`) and references (`\ref{...}`)
* Inline math (`$...$`) and display equation blocks (`\begin{equation}...`)
* Formatting tags (`\textbf{...}`, `\emph{...}`) and LaTeX comments (`%`)

### 3. Sentence Burstiness & Rhythm Meter

Calculates the standard deviation ($\sigma$) of sentence lengths.

* Human writing alternates between punchy short sentences and compound thoughts.
* AI writing typically clusters tightly around 13–17 words per sentence with low variance ($\sigma < 5.0$).

### 4. Interactive Humanizer (`--suggest`)

Provides immediate, context-appropriate human substitutes for common robotic buzzwords:

* `delve` $\rightarrow$ *investigate, examine, analyze*
* `seamless` $\rightarrow$ *smooth, direct, continuous*
* `elevate` $\rightarrow$ *improve, enhance, clarify*

### 5. Visual Heatmap Report (`--report`)

Generates an interactive, standalone `report.html` highlighting flagged vocabulary in red and academic hype in amber directly in your original text.

---

## Command-Line Options

| Flag | Description |
| --- | --- |
| `--mode=academic` | Enables IEEE/research mode (whitelists scientific terms, catches hype) |
| `--mode=general` | Default mode for everyday essays, blogs, and communications |
| `--suggest` | Displays suggested human replacements for flagged words |
| `--report` | Generates a standalone `report.html` visual heatmap |
| `--output=<path>` | Specify custom output destination for the HTML heatmap report |
| `--json` | Outputs raw audit results, burstiness metrics, and suggestions in JSON |
| `--latex` | Forces the LaTeX parser |
| `--markdown` | Forces the Markdown parser |
| `--allow-proof` | Removes score penalty for customer/metric count claims |

---

## Project Structure

```text
GhostTrace/
├── src/
│   └── ghosttrace/
│       ├── __init__.py         # Package exports
│       └── engine.py           # Core detection, parser, and scoring engine
├── tests/
│   └── test_ghosttrace.py      # Unit test suite
├── benchmarks/
│   ├── benchmark_accuracy.py   # Accuracy, recall & precision benchmarking suite
│   └── stress_test.py          # Adversarial edge-case audit
├── examples/
│   ├── sample_ieee.tex         # Sample IEEE LaTeX paper with math & citations
│   └── cleaned.txt             # Exported humanized sample output
├── ghosttrace.py               # Root CLI executable wrapper
├── SKILL.md                    # Agent integration specification
├── README.md                   # Project documentation
└── LICENSE                     # MIT License (dual copyright attribution)
```

---

## Running Tests & Benchmarks

Run unit tests:

```bash
python tests/test_ghosttrace.py
```

Run accuracy validation & benchmarking:

```bash
python benchmarks/benchmark_accuracy.py
```

Run adversarial stress tests:

```bash
python benchmarks/stress_test.py
```

---

## License & Attribution

This project is licensed under the [MIT License](LICENSE).

* Copyright (c) 2026 SHYAM S (GhostTrace Project)
* Portions Copyright (c) 2026 Jack Roberts (SlopMonster)
