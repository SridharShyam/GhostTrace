#!/usr/bin/env python3
"""Validation and accuracy benchmark for GhostTrace.

Evaluates:
  1. Precision & Recall on AI text vs. Human baseline text.
  2. Academic Mode vs. General Mode (False-positive resistance on genuine research).
  3. LaTeX Parser accuracy (handling equations, citations, and formatting).
  4. Burstiness metric accuracy (monotonous AI cadence vs. bursty human rhythm).
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from ghosttrace import (
    audit,
    analyze_burstiness,
    latex_prose,
    markdown_prose,
    humanize_text,
    get_suggestions,
)

# ── Ground Truth Datasets for Benchmarking ────────────────────────────────────

# 1. Obvious AI-Generated Samples (ChatGPT, Claude, Gemini default register)
AI_SAMPLES = [
    # General / Promotional
    "It's not just a product, it's a game-changing journey that empowers users to delve into new realms.",
    "Whether you're an enterprise or a startup, this seamless solution elevates your workflow meticulously.",
    "In today's fast-paced world, unlocking the power of cutting-edge innovation is a testament to progress.",
    "At the end of the day, our bespoke platform streamlines your operations with unparalleled synergy.",
    
    # Academic AI Boilerplate
    "With the rapid development of deep learning, neural architectures have attracted considerable attention.",
    "Extensive experiments have demonstrated that our groundbreaking framework achieves unprecedented accuracy.",
    "To the best of our knowledge, this is the first study to delve into the transformative realm of edge computing.",
]

# 2. Authentic Human Writing Samples (Real academic papers, classical prose, direct human writing)
HUMAN_SAMPLES = [
    # Genuine Academic / IEEE control cases (must NOT be falsely flagged)
    "We present a distributed algorithm for linear quadratic estimation in ad-hoc sensor networks.",
    "Figure 3 plots the empirical convergence rate across twenty Monte Carlo trials.",
    "The proof follows from Bellman's principle of optimality applied to the discrete-time state vector.",
    "We compare the computational complexity of the proposed estimator against standard Kalman filtering.",
    
    # Natural human copy / literature
    "The engine uses four cylinders and runs on standard unleaded fuel.",
    "We built this tool because the existing options took ten minutes to install and crashed constantly.",
    "Call us directly between 9 AM and 5 PM Monday through Friday if you need replacement parts.",
    "The rain began early in the morning and continued without stopping until midnight.",
]

class AccuracyBenchmarkTest(unittest.TestCase):

    def test_ai_sample_detection_recall(self):
        """Test that GhostTrace catches 100% of the synthetic AI samples."""
        detected = 0
        for sample in AI_SAMPLES:
            hits = audit(sample, mode='academic')
            failed_categories = [k for k, v in hits.items() if v]
            if failed_categories:
                detected += 1
        recall = (detected / len(AI_SAMPLES)) * 100
        print(f"\n[BENCHMARK] AI Detection Recall: {recall:.1f}% ({detected}/{len(AI_SAMPLES)})")
        self.assertEqual(recall, 100.0, "GhostTrace should detect 100% of textbook AI samples")

    def test_human_sample_false_positive_resistance(self):
        """Test that GhostTrace does not falsely penalize authentic human writing."""
        clean_count = 0
        for sample in HUMAN_SAMPLES:
            hits = audit(sample, mode='academic')
            failed_categories = [k for k, v in hits.items() if v]
            if not failed_categories:
                clean_count += 1
            else:
                print(f"  [FALSE POSITIVE WARNING]: '{sample}' triggered: {hits}")
        accuracy = (clean_count / len(HUMAN_SAMPLES)) * 100
        print(f"[BENCHMARK] Human Text Clean Rate (Specificity): {accuracy:.1f}% ({clean_count}/{len(HUMAN_SAMPLES)})")
        self.assertEqual(accuracy, 100.0, "Human text should score 5/5 CLEAN without false alarms")

    def test_academic_whitelisting_accuracy(self):
        """Ensure genuine technical terms (e.g. 'robust', 'leverage') don't trigger false positives in academic mode."""
        legitimate_paper = "We analyze the robust stability of the decentralized control loop leveraging Lyapunov theory."
        
        # In general mode: should flag leverage and robust as marketing jargon
        gen_hits = audit(legitimate_paper, mode='general')
        gen_words = [item[0] for item in gen_hits['vocab']]
        self.assertIn('robust', gen_words)
        self.assertIn('leverage', gen_words)

        # In academic mode: MUST be whitelisted and clean
        acad_hits = audit(legitimate_paper, mode='academic')
        acad_words = [item[0] for item in acad_hits['vocab']]
        self.assertNotIn('robust', acad_words)
        self.assertNotIn('leverage', acad_words)
        print(f"[BENCHMARK] Academic Whitelisting: Verified (Technical terms allowed in --mode=academic)")

    def test_latex_cleaning_fidelity(self):
        """Test LaTeX parsing does not leave phantom punctuation or miss hidden AI prose."""
        tex_raw = r"""
        \section{System Model}
        The channel capacity $C = B \log_2(1 + \text{SNR})$ defines the maximum throughput \cite{shannon1948}.
        In this work, we delve into an adaptive strategy.
        \begin{equation}
        \min_{\mathbf{w}} \|\mathbf{y} - \mathbf{H}\mathbf{w}\|^2 + \lambda \|\mathbf{w}\|_1
        \end{equation}
        % Notice: This comment mentions seamless integration but is commented out.
        The resulting structure is not just fast, but robust.
        """
        prose = latex_prose(tex_raw)
        self.assertNotIn("shannon1948", prose)
        self.assertNotIn("comment", prose)
        self.assertNotIn("SNR", prose)
        self.assertIn("In this work, we delve into an adaptive strategy", prose)
        print(f"[BENCHMARK] LaTeX Parser Fidelity: Verified")

    def test_burstiness_accuracy(self):
        """Test that burstiness metric clearly distinguishes monotonous AI text from varied human text."""
        # 10 monotonous sentences of identical length (~8 words)
        monotonous_ai = " ".join([
            f"The network model performs step number {i} accurately." for i in range(12)
        ])
        # 10 human sentences with high variance
        bursty_human = (
            "We measured it. "
            "Although prior researchers assumed that temperature fluctuations would permanently degrade performance across all test chambers, our observations did not show this effect. "
            "It worked. "
            "Specifically, voltage remained stable. "
            "Why did this happen? "
            "The ground conductor was connected to an independent copper sink placed outside the main laboratory chassis. "
            "Then, everything clicked. "
            "Subsequent trials verified the hypothesis across three additional test runs. "
            "No errors appeared. "
            "We conclude that thermal isolation is unnecessary under these boundary constraints."
        )

        ai_metric = analyze_burstiness(monotonous_ai)
        human_metric = analyze_burstiness(bursty_human)

        print(f"[BENCHMARK] AI Cadence Std-Dev: {ai_metric['std_dev']} (Monotonous: {ai_metric['is_monotonous']})")
        print(f"[BENCHMARK] Human Cadence Std-Dev: {human_metric['std_dev']} (Monotonous: {human_metric['is_monotonous']})")

        self.assertTrue(ai_metric['is_monotonous'])
        self.assertFalse(human_metric['is_monotonous'])
        self.assertGreater(human_metric['std_dev'], ai_metric['std_dev'] * 4)

    def test_humanizer_diff_accuracy(self):
        """Verify that humanize_text cleanly replaces AI keywords without destroying text formatting."""
        original = "We delve into this problem to create a seamless interface."
        hits = audit(original, mode='general')
        cleaned, diff = humanize_text(original, hits)
        
        self.assertNotIn("delve", cleaned.lower())
        self.assertNotIn("seamless", cleaned.lower())
        self.assertIn("investigate", cleaned.lower())
        self.assertIn("smooth", cleaned.lower())
        self.assertIn("-We delve", diff)
        self.assertIn("+We investigate", diff)
        print(f"[BENCHMARK] Humanizer Diff Replacement: Verified")

if __name__ == '__main__':
    print("=" * 70)
    print("  GhostTrace Accuracy & Benchmark Suite")
    print("=" * 70)
    unittest.main()
