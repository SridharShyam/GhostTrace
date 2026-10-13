import unittest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))
from ghosttrace import (
    audit,
    analyze_burstiness,
    latex_prose,
    markdown_prose,
    get_suggestions,
)

class TestGhostTrace(unittest.TestCase):

    def test_latex_prose_cleaning(self):
        latex_input = r"""
        \section{Introduction}
        In this work, we test the algorithm.
        Equation $E = mc^2$ governs the dynamics \cite{einstein1905}.
        \begin{equation}
        f(x) = ax + b
        \end{equation}
        % This is a LaTeX comment that should be ignored
        The result is remarkable.
        """
        prose = latex_prose(latex_input)
        self.assertNotIn("cite", prose)
        self.assertNotIn("mc^2", prose)
        self.assertNotIn("f(x)", prose)
        self.assertNotIn("comment", prose)
        self.assertIn("In this work", prose)

    def test_academic_mode_whitelists(self):
        # In academic mode, 'robust' and 'leverage' should be tolerated
        academic_hits = audit("We develop a robust framework leveraging convex optimization.", mode='academic')
        vocab_words = [item[0] for item in academic_hits['vocab']]
        self.assertNotIn('robust', vocab_words)
        self.assertNotIn('leverage', vocab_words)

        # In general mode, they should be flagged as marketing jargon
        general_hits = audit("We develop a robust framework leveraging convex optimization.", mode='general')
        general_vocab = [item[0] for item in general_hits['vocab']]
        self.assertIn('robust', general_vocab)
        self.assertIn('leverage', general_vocab)

    def test_academic_boilerplate_detection(self):
        paper_snippet = "With the rapid development of deep learning, attention mechanisms have attracted considerable attention."
        hits = audit(paper_snippet, mode='academic')
        phrase_labels = [item[0] for item in hits['phrases']]
        self.assertIn('boilerplate paper opener', phrase_labels)
        self.assertIn('cliche literature review hook', phrase_labels)

    def test_burstiness_metric(self):
        # Monotonous sentences (similar length)
        monotonous_text = (
            "The model processes data accurately. "
            "The system evaluates results smoothly. "
            "The method calculates values directly. "
            "The network predicts outputs cleanly. "
            "The server responds quickly today. "
            "The client receives signals nicely. "
            "The device charges battery safely. "
            "The engine drives motion steadily. "
            "The sensor records inputs properly. "
            "The display renders graphics neatly."
        )
        burst = analyze_burstiness(monotonous_text)
        self.assertTrue(burst['is_monotonous'])
        self.assertLess(burst['std_dev'], 2.0)

    def test_synonym_suggestions(self):
        hits = audit("We delve into the seamless data architecture.", mode='general')
        suggestions = dict(get_suggestions(hits))
        self.assertIn('delve', suggestions)
        self.assertIn('investigate', suggestions['delve'])
        self.assertIn('seamless', suggestions)
        self.assertIn('smooth', suggestions['seamless'])

if __name__ == '__main__':
    unittest.main()
