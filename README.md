# GhostTrace

> **Deterministic AI Trace & Slop Detection Engine**  
> Uncover subtle AI writing fingerprints, promotional filler, flat burstiness cadences, and model-specific tells across General, Academic (IEEE/Research), and Technical documents.

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python 3](https://img.shields.io/badge/Python-3.8%2B-green.svg)
![CI](https://github.com/SridharShyam/GhostTrace/actions/workflows/ci.yml/badge.svg)
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
6. **Cross-Platform Auto-Cleanse:** Re-edits and cleanses drafts using alternate models or local LLMs.
7. **100% Offline & Private:** Zero cloud API dependencies; your unpublished research never leaves your machine.

---

## Quick Start

### Installation

Install globally or in editable mode via pip:

```bash
git clone https://github.com/SridharShyam/GhostTrace.git
cd GhostTrace
pip install -e .
```

Once installed, you can invoke `ghosttrace` anywhere from your terminal. Or run it directly without installing:

```bash
python ghosttrace.py --text "In this paper, we delve into a revolutionary approach." --suggest
```

### Usage Examples

```bash
# 1. Launch the interactive browser Web UI with live heatmap and confirmation editor
ghosttrace ui

# 2. Audit a short draft with replacement suggestions
ghosttrace --text "In this paper, we delve into a revolutionary approach that provides seamless optimization." --suggest

# 3. Audit an IEEE LaTeX paper and generate a visual heatmap report
ghosttrace examples/sample_ieee.tex --mode=academic --report --suggest

# 4. View unified diff of humanized substitutions and export cleaned copy
ghosttrace examples/sample_ieee.tex --diff --clean=cleaned_paper.tex

# 5. Run cross-model AI cleanser pass using a local or rival CLI model
ghosttrace cleanse examples/sample_ieee.tex --model-cli="ollama run llama3" -o paper_cleansed.tex

# 6. Print copy-paste editorial prompt for ChatGPT/Claude web chat
ghosttrace cleanse examples/sample_ieee.tex --print-prompt
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

## 5 Novel Enterprise Subsystems

GhostTrace incorporates five specialized subsystems designed to catch modern LLM watermarks, provenance signatures, citation confabulations, and translation patterns:

1. **Synthetic Token Watermark Analyzer (Kirchenbauer et al.)**:
   * Analyzes bigram token transitions using rolling pseudorandom hash partitions.
   * Calculates empirical green-list token ratios and evaluates the one-tailed Gaussian $Z$-score ($z \ge 3.0$ flags active statistical watermarking with $p < 0.0013$).
   * REST API: `POST /api/features/token-watermark`

2. **Model Provenance Fingerprinter**:
   * Pinpoints LLM family provenance (**OpenAI GPT-4o**, **Anthropic Claude 3.5**, or **Google Gemini 1.5/2.0**) by analyzing rhetorical framing, meta-qualifiers (*"it is important to remember"*, *"it's worth noting"*, *"here's the breakdown"*), and characteristic em-dash clause-bracketing.
   * REST API: `POST /api/features/provenance`

3. **Adversarial Citation & Hallucinated Reference Auditor**:
   * Cross-audits academic bibliographies, formatted DOIs (`10.NNNN/...`), and arXiv identifiers (`YYMM.NNNNN`).
   * Flags impossible future publication years ($> 2026$) and confabulated synthetic journal titles (*"Journal of Advanced Machine Learning Innovations"*).
   * REST API: `POST /api/features/citations`

4. **Cross-Language & Translation AI Artifact Detector**:
   * Traps syntactic calques, false friends, and structural translationese injected by multilingual LLMs translating thought patterns from Germanic (*"in the rule"*, *"bring to expression"*), French (*"permits to..."*, *"in a first time"*), and Spanish/Italian (*"make reference to"*, *"in base to"*).
   * REST API: `POST /api/features/translation-artifacts`

5. **Local N-Gram Glider & Perplexity Cadence Profiler**:
   * Detects robotic anaphora head-word stacking (consecutive sentences opening with identical subjects/verbs) and recycled 3-gram and 4-gram phrasal repetitions alongside Type-Token Ratio (TTR) lexical diversity profiling.
   * REST API: `POST /api/features/ngram-profile`

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
├── frontend/                   # Standalone Frontend workspace
│   ├── public/
│   │   └── index.html          # Clean Unstop Light Theme single-page application
│   └── src/
│       ├── app.js              # Real-time debounced audit client & review queue
│       └── style.css           # Pure CSS design system & typography
├── src/
│   └── ghosttrace/
│       ├── __init__.py         # Package exports & public API
│       ├── engine.py           # Core detection, burstiness math & watermark engine
│       ├── cleanse.py          # Second-pass AI-to-AI humanizer & LLM bridge
│       └── ui/
│           ├── server.py       # Multi-threaded HTTP server, REST APIs & Swagger UI
│           ├── extractor.py    # Document extractor (.docx, .pdf, .zip, .tex, .md, .txt)
│           ├── templates/      # Packaged template fallback
│           └── static/         # Packaged static assets fallback
├── tests/
│   ├── test_ghosttrace.py      # Core functional tests
│   └── test_error_handling.py  # Robustness & security edge-case tests
├── benchmarks/
│   ├── benchmark_accuracy.py   # Accuracy, recall & precision benchmark suite
│   └── stress_test.py          # Adversarial edge-case audit
├── examples/
│   ├── sample_ieee.tex         # Sample IEEE LaTeX paper with math & citations
│   └── cleaned.txt             # Exported humanized sample output
├── ghosttrace.py               # Root CLI executable launcher shim
├── pyproject.toml              # PEP 517/621 packaging configuration
├── README.md                   # Project documentation
└── LICENSE                     # MIT License
```

---

## Interactive REST API & Swagger UI

When running `ghosttrace ui`, an interactive OpenAPI/Swagger testing portal is automatically available:

* **Swagger Documentation:** [http://localhost:7860/docs](http://localhost:7860/docs)
* **OpenAPI 3.0 Specification:** [http://localhost:7860/openapi.json](http://localhost:7860/openapi.json)

Available REST endpoints:

* `POST /api/audit`: Full composite audit pipeline (including provenance, watermarks, and citation integrity).
* `POST /api/burstiness`: Sentence length variance and cadence profiling.
* `POST /api/watermarks/detect`: Scans text for zero-width steganographic markers.
* `POST /api/watermarks/purge`: Strips invisible watermarks and returns cleaned text.
* `POST /api/suggestions`: Returns curated human synonym recommendations.
* `POST /api/humanize`: Replaces AI tells and returns humanized text with a diff.
* `POST /api/upload`: Safe multi-format document extraction.
* `POST /api/features/token-watermark`: Kirchenbauer statistical green/red list token watermark analyzer.
* `POST /api/features/provenance`: Model family signature classifier (GPT vs Claude vs Gemini).
* `POST /api/features/citations`: DOI, arXiv format, and hallucinated reference auditor.
* `POST /api/features/translation-artifacts`: Syntactic calques and multilingual translationese detector.
* `POST /api/features/ngram-profile`: Repetitive anaphora head-word stacking and N-gram perplexity glider.

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
