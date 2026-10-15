import io
import unittest
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from ghosttrace import (
    audit,
    analyze_burstiness,
    calculate_score,
    latex_prose,
    markdown_prose,
    detect_watermarks,
    sanitize_watermarks,
    get_suggestions,
)
from ghosttrace.ui.extractor import extract_text_from_file

class TestGhostTraceErrorHandlingAndEdgeCases(unittest.TestCase):

    def test_empty_string_input(self):
        """Empty input should not raise exception and produce sensible zero/empty results."""
        hits = audit("", mode="general")
        self.assertEqual(len(hits['vocab']), 0)
        self.assertEqual(len(hits['phrases']), 0)
        burst = analyze_burstiness("")
        self.assertEqual(burst['std_dev'], 0)
        self.assertEqual(burst['sentence_lengths'], [])
        score, total_vocab, density_penalty, total_phrases = calculate_score(hits, word_count=0, burst=burst)
        self.assertEqual(score, 5)

    def test_pure_whitespace_and_newlines(self):
        """Whitespace-only and multi-newline strings should be handled gracefully."""
        hits = audit("   \n\n\t\r\n   ", mode="academic")
        self.assertEqual(len(hits['vocab']), 0)
        burst = analyze_burstiness("   \n\n\t\r\n   ")
        self.assertEqual(burst['entropy'], 0.0)

    def test_single_word_or_short_fragment(self):
        """Fragments shorter than 3 words shouldn't break sentence calculations."""
        burst = analyze_burstiness("Hello world.")
        self.assertEqual(burst['score'], 'N/A (text too short)')
        self.assertFalse(burst['is_monotonous'])

    def test_heavy_unicode_emojis_and_multilingual(self):
        """Non-Latin and emoji inputs should not cause decoding errors or crashes."""
        multilingual_text = "வணக்கம் உலகம்! 🚀✨ This is a test with emojis and UTF-8 characters: Привет мир, こんにちは, 你好世界."
        hits = audit(multilingual_text, mode="general")
        self.assertIsInstance(hits, dict)
        burst = analyze_burstiness(multilingual_text)
        self.assertIn('entropy', burst)

    def test_unclosed_latex_and_corrupt_markdown(self):
        """Malformed LaTeX or Markdown shouldn't crash parser."""
        bad_latex = r"\section{Broken \begin{equation} $x + y"
        cleaned_latex = latex_prose(bad_latex)
        self.assertIsInstance(cleaned_latex, str)

        bad_md = "## Incomplete link [test](http://..."
        cleaned_md = markdown_prose(bad_md)
        self.assertIsInstance(cleaned_md, str)

    def test_huge_input_performance(self):
        """Stress-test with a 50,000 word simulated text block."""
        large_text = ("This is a repetitive sentence testing performance and memory stability. " * 3000)
        hits = audit(large_text, mode="general")
        self.assertIsInstance(hits, dict)
        burst = analyze_burstiness(large_text)
        self.assertTrue(burst['is_monotonous'])

    def test_file_extractor_unsupported_and_corrupted_file(self):
        """Ensure corrupted binary files and unknown extensions do not crash extractor."""
        # Random corrupt bytes passed as docx
        corrupted_docx = b"PK\x03\x04randomcorruptbinarydatahere"
        result = extract_text_from_file("corrupted.docx", corrupted_docx)
        self.assertTrue("[Error extracting text from Word document" in result or "docx" in result)

        # Corrupt PDF bytes
        corrupted_pdf = b"%PDF-1.4 corrupt junk content"
        result_pdf = extract_text_from_file("corrupted.pdf", corrupted_pdf)
        self.assertTrue("[Error extracting text from PDF" in result_pdf or isinstance(result_pdf, str))

        # Corrupt ZIP archive
        corrupted_zip = b"PK\x03\x04fakezipheader"
        result_zip = extract_text_from_file("corrupted.zip", corrupted_zip)
        self.assertTrue("[Error extracting ZIP archive" in result_zip or isinstance(result_zip, str))

        # Unknown extension fallback
        unknown_ext = extract_text_from_file("data.xyz", b"Sample raw line content")
        self.assertEqual(unknown_ext, "Sample raw line content")

    def test_massive_watermark_bomb(self):
        """Text loaded with thousands of invisible zero-width characters."""
        bomb = "Normal start " + ("\u200B\u200C\u200D\uFEFF" * 1000) + " normal end."
        detected = detect_watermarks(bomb)
        self.assertEqual(detected['Zero-Width Space (ZWSP)'], 1000)
        self.assertEqual(detected['Zero-Width Non-Joiner (ZWNJ)'], 1000)
        clean = sanitize_watermarks(bomb)
        self.assertEqual(len(detect_watermarks(clean)), 0)
        self.assertEqual(clean.strip(), "Normal start  normal end.")

if __name__ == '__main__':
    unittest.main()
