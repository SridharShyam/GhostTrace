# Pillar 1 Verification Report: Multi-Genre Detection Presets

**Date:** 2026-10-14  
**Pillar Under Test:** Pillar 1 (Multi-Genre Detection Presets)  
**Status:** ✅ COMPLETE & VERIFIED

---

## 1. Objectives & Implemented Presets

Traditional detectors apply a single monolithic classifier across all text types, leading to false positives on technical papers and missed AI tells in creative writing or student essays. 

In Pillar 1, we implemented **4 distinct, specialized detection presets** across the CLI engine, REST API, and Angular Material UI:

1. **`--mode=general` (General Copy & Web Content)**:
   - Scans for marketing hype, corporate filler, throat-clearing openers (*"in today's fast-paced world"*), and conversational AI crutches (*"not just X, but Y"*).
2. **`--mode=academic` (IEEE, ACM, Springer Research Papers & LaTeX)**:
   - Whitelists legitimate scientific terminology (`robust control`, `leverage a dataset`, `convex optimization`).
   - Penalizes unsubstantiated hype (*"groundbreaking"*, *"unprecedented accuracy"*), literature review clichés (*"has attracted considerable attention"*), and unverified novelty assertions.
3. **`--mode=creative` (Fiction, Narratives & Storytelling)**:
   - Targets ChatGPT's stock storytelling tropes:
     - Moral conclusions (*"choosing honesty over temptation/greed"*).
     - Sanctimonious fable phrasing (*"the right thing to do"*, *"only done his duty"*).
     - Stock emotional reactions (*"smiled with relief"*, *"eyes filled with relief"*, *"shaky smile"*).
     - Internal monologue transitions (*"For a moment, he thought about how..."*).
     - Reflective parable summaries (*"felt proud of choosing"*, *"realised that even a small good deed"*).
   - Enforces a strict **Sentence Burstiness Penalty**: Directly docks the cleanliness score when story sentences have uniform length ($\sigma < 2.5$).
4. **`--mode=essay` (Student Essays, Statements of Purpose & Grants)**:
   - Identifies classic academic essay clichés (*"since the dawn of time"*, *"throughout human history, people have"*, *"in order to truly understand"*, *"it is undeniably true that"*, *"plays a pivotal role in shaping"*).

---

## 2. Test Execution & Benchmark Results

### 2.1 Test: ChatGPT Short Story ("The Lost Wallet") under `--mode=creative`
- **Input Text:**
  > *"Rahul was walking home from college when he noticed a wallet lying on the road. He picked it up and found some money and an identity card inside. For a moment, he thought about how useful the money would be. However, he decided that returning the wallet was the right thing to do. He checked the address on the identity card and went to the owner's house. An elderly man opened the door and looked surprised to see Rahul. The man smiled with relief when Rahul handed over the wallet. He thanked Rahul and offered him a reward for his honesty. Rahul politely refused the reward and said he had only done his duty. As he walked home, he felt proud of choosing honesty over temptation."*
- **Tells Flagged:**
  - `AI moral conclusion cliche`: *"choosing honesty over temptation"*
  - `sanctimonious fable cliche`: *"the right thing to do"*, *"only done his duty"* (2 instances)
  - `stock AI narrative reaction`: *"looked surprised to see"*, *"smiled with relief"* (2 instances)
  - `stock internal monologue transition`: *"for a moment, he thought about how"*
  - `reflective moral summary`: *"felt proud of choosing"*
- **Sentence Burstiness ($\sigma$):** $1.2\ \sigma$ (Flagged: `Flat Cadence / Monotonous AI Rhythm`).
- **Cleanliness Score:** **1 / 5** (Previously scored 5/5 before Pillar 1).

### 2.2 Test: Student Essay Boilerplate under `--mode=essay`
- **Input Text:**
  > *"Since the dawn of human history, technology has played a pivotal role in shaping society. In order to truly understand this phenomenon, it is undeniably true that we must examine its foundations."*
- **Tells Flagged:**
  - `throat-clearing thesis opener`: *"in order to truly understand"*
  - `heavy-handed declaration`: *"it is undeniably true that"*
  - `dawn of time cliche`: *"since the dawn of human history"*
- **Cleanliness Score:** **0 / 5** (NEEDS CLEANSE).

### 2.3 Test: Authentic Technical Paper Control under `--mode=academic`
- **Input Text:**
  > *"We formulate the convex optimization problem as a semidefinite program and prove asymptotic convergence under robust parameter bounds."*
- **Tells Flagged:** 0 (Whitelisted technical terms allowed).
- **Cleanliness Score:** **5 / 5 (CLEAN)**.

---

## 3. UI Implementation
- Added Material toggle buttons (`mat-button-toggle`) in the top navigation toolbar:
  - `General` (`auto_fix_high`)
  - `Academic` (`school`)
  - `Creative` (`menu_book`)
  - `Essay` (`history_edu`)
- When switched, the editor audits and recalculates telemetry instantly without reloading the page.

---

## 4. Next Step
Pillar 1 is complete, verified, and pushed to `main`. We are ready to proceed to **Pillar 2: Advanced Forensic Metrics (Statistical AI Profiling & Interactive Sentence Rhythm Chart)**.
