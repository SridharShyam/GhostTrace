import unittest
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from ghosttrace import (
    detect_synthetic_token_watermark,
    detect_model_provenance,
    audit_citations,
    detect_translation_artifacts,
    profile_ngrams_and_perplexity,
)

class TestNovelFeatures(unittest.TestCase):

    def test_synthetic_token_watermark_short_text(self):
        text = "Hello world short"
        res = detect_synthetic_token_watermark(text)
        self.assertFalse(res['is_watermarked'])
        self.assertIn("too short", res['verdict'].lower())

    def test_synthetic_token_watermark_calculation(self):
        text = "Deep neural networks have revolutionized natural language processing and computer vision across numerous benchmark tasks and scientific disciplines with remarkable empirical performance."
        res = detect_synthetic_token_watermark(text)
        self.assertIn('z_score', res)
        self.assertIn('green_tokens', res)
        self.assertIn('green_ratio', res)
        self.assertIn('is_watermarked', res)
        self.assertGreaterEqual(res['total_tokens'], 10)

    def test_model_provenance_detection(self):
        gpt_text = "It is important to remember that we should delve into this fast-paced world to streamline our workflow. In conclusion, this is vital."
        claude_text = "It's worth noting that this is a nuanced distinction. Furthermore, on balance it's fair to say there is a fascinating dynamic."
        gemini_text = "Let's break down the key takeaways. Think of it as a deep dive into the secret sauce and bottom line."

        gpt_res = detect_model_provenance(gpt_text)
        self.assertEqual(gpt_res['predicted_model'], 'OpenAI (GPT-4o / ChatGPT)')
        self.assertGreater(gpt_res['probabilities']['gpt'], 40)

        claude_res = detect_model_provenance(claude_text)
        self.assertEqual(claude_res['predicted_model'], 'Anthropic (Claude 3.5 Sonnet / Opus)')
        self.assertGreater(claude_res['probabilities']['claude'], 40)

        gemini_res = detect_model_provenance(gemini_text)
        self.assertEqual(gemini_res['predicted_model'], 'Google (Gemini 1.5 / 2.0)')
        self.assertGreater(gemini_res['probabilities']['gemini'], 40)

    def test_audit_citations_valid_and_hallucinations(self):
        valid_sample = "Refer to the initial study at https://doi.org/10.1038/s41586-020-2649-2 and arXiv:2303.08774."
        valid_res = audit_citations(valid_sample)
        self.assertEqual(len(valid_res['invalid_dois']), 0)
        self.assertEqual(len(valid_res['invalid_arxiv_ids']), 0)
        self.assertGreaterEqual(len(valid_res['valid_dois']), 1)
        self.assertGreaterEqual(len(valid_res['valid_arxiv_ids']), 1)
        self.assertEqual(valid_res['citation_integrity_score'], 100)

        hallucinated_sample = "See arXiv:9914.99999 in Frontiers in Transformative Neural Computing (2045)."
        hall_res = audit_citations(hallucinated_sample)
        self.assertGreaterEqual(len(hall_res['invalid_arxiv_ids']), 1)
        self.assertGreaterEqual(len(hall_res['suspicious_patterns']), 2)
        self.assertLess(hall_res['citation_integrity_score'], 80)

    def test_translation_artifacts(self):
        calque_text = "In the rule, this method permits to optimize latency. We must have in account these facts."
        res = detect_translation_artifacts(calque_text)
        self.assertTrue(res['has_translation_artifacts'])
        self.assertGreaterEqual(res['total_artifacts'], 2)
        self.assertIn('Germanic', [a['origin_family'] for a in res['artifacts']])
        self.assertIn('Spanish Italian', [a['origin_family'] for a in res['artifacts']])

    def test_profile_ngrams_and_perplexity(self):
        repetitive_anaphora = (
            "The model processes data accurately. "
            "The model processes data reliably. "
            "The model processes data continuously. "
            "The model processes data efficiently."
        )
        res = profile_ngrams_and_perplexity(repetitive_anaphora)
        self.assertTrue(res['is_robotic_cadence'])
        self.assertGreaterEqual(len(res['consecutive_head_word_stacking']), 2)
        self.assertGreaterEqual(len(res['recycled_ngrams']), 1)
        self.assertEqual(res['sentence_count'], 4)

if __name__ == '__main__':
    unittest.main()
