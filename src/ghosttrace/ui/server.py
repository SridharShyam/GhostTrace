#!/usr/bin/env python3
"""HTTP server and REST API for GhostTrace.

Serves the web application and provides endpoints for text analysis,
burstiness profiling, watermark detection, and synonym substitution.
"""

import email
import http.server
import json
import os
import socketserver
import sys
import urllib.parse
import webbrowser

from ghosttrace.engine import (
    audit,
    analyze_burstiness,
    calculate_score,
    latex_prose,
    markdown_prose,
    visible_text_html,
    detect_watermarks,
    sanitize_watermarks,
    humanize_text,
    get_suggestions,
    detect_synthetic_token_watermark,
    detect_model_provenance,
    audit_citations,
    detect_translation_artifacts,
    profile_ngrams_and_perplexity,
)
from ghosttrace.ui.extractor import extract_text_from_file
from ghosttrace.config import (
    HOST as DEFAULT_HOST,
    PORT as DEFAULT_PORT,
    MAX_PAYLOAD_SIZE,
)

UI_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(UI_DIR, "static")
TEMPLATES_DIR = os.path.join(UI_DIR, "templates")

# Path resolution for standalone frontend development
PROJECT_ROOT = os.path.abspath(os.path.join(UI_DIR, "..", "..", ".."))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
FRONTEND_SRC = os.path.join(FRONTEND_DIR, "src")
FRONTEND_PUBLIC = os.path.join(FRONTEND_DIR, "public")

class GhostTraceHandler(http.server.SimpleHTTPRequestHandler):
    """Handles static assets and API requests for the application."""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Serve clean Unstop Light Theme HTML & Static Assets directly
        if path in ['/', '/index.html']:
            index_file = os.path.join(FRONTEND_PUBLIC, 'index.html')
            if not os.path.exists(index_file):
                index_file = os.path.join(TEMPLATES_DIR, 'index.html')
            with open(index_file, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if path.startswith('/static/'):
            filename = os.path.basename(path)
            file_path = os.path.join(FRONTEND_SRC, filename)
            if not os.path.exists(file_path):
                file_path = os.path.join(STATIC_DIR, filename)

            if os.path.exists(file_path):
                content_type = 'text/css' if filename.endswith('.css') else 'application/javascript'
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        # Interactive Swagger UI & OpenAPI Specification
        if path in ['/docs', '/docs/', '/swagger', '/swagger/']:
            swagger_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GhostTrace API — Swagger UI</title>
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  <style>
    body { margin: 0; background: #fafafa; }
    .topbar { display: none; }
    .swagger-ui .info { margin: 25px 0; }
    .swagger-ui .info .title { font-family: sans-serif; color: #1c4980; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js" crossorigin></script>
  <script>
    window.onload = () => {
      window.ui = SwaggerUIBundle({
        url: '/openapi.json',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [SwaggerUIBundle.presets.apis],
        layout: "BaseLayout"
      });
    };
  </script>
</body>
</html>"""
            content = swagger_html.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if path == '/openapi.json':
            spec = {
                "openapi": "3.0.3",
                "info": {
                    "title": "GhostTrace REST API",
                    "description": "Zero-trust, deterministic AI slop detection, sentence burstiness rhythm analysis, watermark purger, and humanizer.",
                    "version": "2.2.0"
                },
                "tags": [
                    {"name": "Full Audit", "description": "Complete multi-metric text audit pipeline"},
                    {"name": "Burstiness & Rhythm", "description": "Sentence length variance and structural cadence profiling"},
                    {"name": "Watermarks & Steganography", "description": "Zero-width character and steganographic marker detection/sanitization"},
                    {"name": "Humanizer & Synonyms", "description": "Explainable synonym suggestions and automated humanizing"},
                    {"name": "Novel Enterprise Subsystems", "description": "Kirchenbauer Token Watermarks, Model Provenance, Citation Auditor, Translation Artifacts, N-Gram Glider"},
                    {"name": "Documents", "description": "Multi-format document parsing and extraction"}
                ],
                "paths": {
                    "/api/audit": {
                        "post": {
                            "tags": ["Full Audit"],
                            "summary": "Full Composite Audit",
                            "description": "Analyze text for AI vocabulary tells, marketing slop, burstiness, steganographic watermarks, and get human synonym suggestions in one roundtrip.",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string", "example": "In this paper, we delve into a transformative paradigm that provides seamless optimization."},
                                                "mode": {"type": "string", "enum": ["general", "academic", "creative", "essay"], "default": "general"}
                                            },
                                            "required": ["text"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {"description": "Audit Results"}
                            }
                        }
                    },
                    "/api/burstiness": {
                        "post": {
                            "tags": ["Burstiness & Rhythm"],
                            "summary": "Calculate Sentence Burstiness",
                            "description": "Calculates sentence count, average length, standard deviation (variance σ), entropy, and detects monotonous robotic AI cadences.",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string", "example": "This is a short sentence. However, human writing naturally mixes short direct statements with significantly longer, compound formulations to create engaging rhythm."}
                                            },
                                            "required": ["text"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {"description": "Burstiness Metrics"}
                            }
                        }
                    },
                    "/api/watermarks/detect": {
                        "post": {
                            "tags": ["Watermarks & Steganography"],
                            "summary": "Detect Zero-Width Watermarks",
                            "description": "Scans text for hidden zero-width spaces, joiners, exotic Unicode spaces, and abnormal em-dash frequencies.",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string", "example": "Clean text without steganography."}
                                            },
                                            "required": ["text"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {"description": "Detected watermarks breakdown"}
                            }
                        }
                    },
                    "/api/watermarks/purge": {
                        "post": {
                            "tags": ["Watermarks & Steganography"],
                            "summary": "Purge Zero-Width Watermarks",
                            "description": "Strips all invisible zero-width characters, normalizes unusual Unicode whitespace, and returns cleansed text.",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string", "example": "Text with possible\u200B zero-width\u200C markers."},
                                                "soften_em_dashes": {"type": "boolean", "default": False}
                                            },
                                            "required": ["text"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {"description": "Sanitized text"}
                            }
                        }
                    },
                    "/api/suggestions": {
                        "post": {
                            "tags": ["Humanizer & Synonyms"],
                            "summary": "Get Human Synonym Suggestions",
                            "description": "Analyzes text for AI vocabulary buzzwords and returns curated, human synonym replacements.",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string", "example": "We delve into this seamless approach to unlock efficiency."},
                                                "mode": {"type": "string", "enum": ["general", "academic", "creative", "essay"], "default": "general"}
                                            },
                                            "required": ["text"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {"description": "Dictionary of suggestions"}
                            }
                        }
                    },
                    "/api/humanize": {
                        "post": {
                            "tags": ["Humanizer & Synonyms"],
                            "summary": "Humanize Text",
                            "description": "Automatically replaces AI vocabulary with natural human synonyms, purges watermarks, and returns humanized text plus a unified diff.",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string", "example": "We delve into a transformative realm that provides seamless optimization."},
                                                "mode": {"type": "string", "enum": ["general", "academic", "creative", "essay"], "default": "general"},
                                                "randomize": {"type": "boolean", "default": True},
                                                "soften_em_dashes": {"type": "boolean", "default": False}
                                            },
                                            "required": ["text"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {"description": "Humanized text and diff"}
                            }
                        }
                    },
                    "/api/upload": {
                        "post": {
                            "tags": ["Documents"],
                            "summary": "Upload and Extract Document",
                            "description": "Extract raw text from .docx, .pdf, .tex, .md, .txt, or .zip archives with built-in decompression bomb guards.",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "multipart/form-data": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "file": {
                                                    "type": "string",
                                                    "format": "binary"
                                                }
                                            },
                                            "required": ["file"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Document text extracted successfully"
                                }
                            }
                        }
                    },
                    "/api/features/token-watermark": {
                        "post": {
                            "tags": ["Novel Enterprise Subsystems"],
                            "summary": "Synthetic Token Watermark (Kirchenbauer et al. Model)",
                            "description": "Analyzes bigram pseudo-random green-red list clustering and calculates the one-tailed z-score to spot server-side statistical watermarks.",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string", "example": "The model meticulously optimizes parameters across the transformative framework."}
                                            },
                                            "required": ["text"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {"description": "Token watermark z-score and statistical metrics"}
                            }
                        }
                    },
                    "/api/features/provenance": {
                        "post": {
                            "tags": ["Novel Enterprise Subsystems"],
                            "summary": "Model Provenance Fingerprinter",
                            "description": "Identifies model-family syntactical idioms to determine whether text was generated by OpenAI GPT-4o, Anthropic Claude 3.5, or Google Gemini.",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string", "example": "It's worth pointing out that this nuanced interplay strikes a balance between efficiency and complexity."}
                                            },
                                            "required": ["text"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {"description": "Model provenance probabilities and detected signatures"}
                            }
                        }
                    },
                    "/api/features/citations": {
                        "post": {
                            "tags": ["Novel Enterprise Subsystems"],
                            "summary": "Adversarial Citation & Hallucination Auditor",
                            "description": "Scans citations for valid DOIs, arXiv format validity (YYMM.NNNN), future year hallucinations, and synthetic journal confabulations.",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string", "example": "Recent progress (arXiv:2305.12345) and studies published in 10.1038/s41586-020-2649-2 demonstrate convergence."}
                                            },
                                            "required": ["text"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {"description": "Citation integrity metrics and hallucination alerts"}
                            }
                        }
                    },
                    "/api/features/translation-artifacts": {
                        "post": {
                            "tags": ["Novel Enterprise Subsystems"],
                            "summary": "Cross-Language & Translation AI Artifact Detector",
                            "description": "Detects syntactic calques, false friends, and machine translation artifacts from Germanic, French, and Romance LLM translation pipelines.",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string", "example": "In the rule, this method permits to optimize the actual state of convergence."}
                                            },
                                            "required": ["text"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {"description": "Detected translation calques and human rephrasings"}
                            }
                        }
                    },
                    "/api/features/ngram-profile": {
                        "post": {
                            "tags": ["Novel Enterprise Subsystems"],
                            "summary": "Local N-Gram Glider & Perplexity Cadence Profiler",
                            "description": "Glides across sentences to detect consecutive head word stacking (anaphora), recycled trigrams, and lexical diversity ratios (TTR).",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string", "example": "The model demonstrates high precision. The model achieves rapid convergence. Furthermore, we observe minimal latency."}
                                            },
                                            "required": ["text"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {"description": "N-gram cadence report and anaphora alerts"}
                            }
                        }
                    }
                }
            }
            content = json.dumps(spec, indent=2).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        self.send_error(404, "File not found")

    def _read_json_body(self):
        """Helper to read and decode JSON request body safely with strict=False."""
        length = int(self.headers.get('Content-Length', 0))
        if length > MAX_PAYLOAD_SIZE:
            return None, "Payload exceeds maximum limit of 25MB."
        body = self.rfile.read(length).decode('utf-8', errors='replace')
        try:
            data = json.loads(body, strict=False) if body.strip() else {}
            return data, None
        except Exception as e:
            return None, f"Invalid JSON format: {str(e)}"

    def _send_json_response(self, code, data):
        """Helper to serialize and transmit JSON response."""
        resp_bytes = json.dumps(data).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(resp_bytes)))
        self.end_headers()
        self.wfile.write(resp_bytes)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. Full Composite Audit API
        if path == '/api/audit':
            data, err = self._read_json_body()
            if err:
                code = 413 if '25MB' in err else 400
                self._send_json_response(code, {'error': err})
                return

            try:
                raw_text = data.get('text', '')
                mode = data.get('mode', 'general')

                parsed_text = raw_text
                if mode == 'academic' and ('\\section' in raw_text or '\\begin' in raw_text or '\\cite' in raw_text):
                    parsed_text = latex_prose(raw_text)

                hits = audit(parsed_text, mode=mode)
                burst = analyze_burstiness(parsed_text)
                word_count = len(parsed_text.split())
                score, total_vocab, density_penalty, total_phrases = calculate_score(hits, word_count=word_count, burst=burst)
                watermarks = detect_watermarks(raw_text)
                suggestions = dict(get_suggestions(hits))

                # Enterprise novel analysis modules
                token_watermark = detect_synthetic_token_watermark(parsed_text)
                provenance = detect_model_provenance(parsed_text)
                citation_audit = audit_citations(raw_text)
                translation_artifacts = detect_translation_artifacts(parsed_text)
                ngram_profile = profile_ngrams_and_perplexity(parsed_text)

                response = {
                    'mode': mode,
                    'word_count': word_count,
                    'score': score,
                    'hits': hits,
                    'burstiness': burst,
                    'watermarks': watermarks,
                    'suggestions': suggestions,
                    'provenance': provenance,
                    'token_watermark': token_watermark,
                    'citation_audit': citation_audit,
                    'translation_artifacts': translation_artifacts,
                    'ngram_profile': ngram_profile
                }
                self._send_json_response(200, response)
            except Exception as e:
                self._send_json_response(500, {'error': f'Audit processing failed: {str(e)}'})
            return

        # 2. Granular: Sentence Burstiness & Rhythm Analysis API
        if path == '/api/burstiness':
            data, err = self._read_json_body()
            if err:
                code = 413 if '25MB' in err else 400
                self._send_json_response(code, {'error': err})
                return

            try:
                raw_text = data.get('text', '')
                burst = analyze_burstiness(raw_text)
                self._send_json_response(200, burst)
            except Exception as e:
                self._send_json_response(500, {'error': f'Burstiness calculation failed: {str(e)}'})
            return

        # 3. Granular: Watermark & Steganography Detection API
        if path == '/api/watermarks/detect':
            data, err = self._read_json_body()
            if err:
                code = 413 if '25MB' in err else 400
                self._send_json_response(code, {'error': err})
                return

            try:
                raw_text = data.get('text', '')
                watermarks = detect_watermarks(raw_text)
                self._send_json_response(200, {'watermarks': watermarks, 'count': sum(watermarks.values())})
            except Exception as e:
                self._send_json_response(500, {'error': f'Watermark detection failed: {str(e)}'})
            return

        # 4. Granular: Watermark Purge & Sanitization API
        if path == '/api/watermarks/purge':
            data, err = self._read_json_body()
            if err:
                code = 413 if '25MB' in err else 400
                self._send_json_response(code, {'error': err})
                return

            try:
                raw_text = data.get('text', '')
                soften_em_dashes = data.get('soften_em_dashes', False)
                clean_text = sanitize_watermarks(raw_text, replace_em_dashes=soften_em_dashes)
                self._send_json_response(200, {'cleaned_text': clean_text})
            except Exception as e:
                self._send_json_response(500, {'error': f'Watermark purge failed: {str(e)}'})
            return

        # 5. Granular: Synonym Suggestions API
        if path == '/api/suggestions':
            data, err = self._read_json_body()
            if err:
                code = 413 if '25MB' in err else 400
                self._send_json_response(code, {'error': err})
                return

            try:
                raw_text = data.get('text', '')
                mode = data.get('mode', 'general')
                hits = audit(raw_text, mode=mode)
                suggestions = dict(get_suggestions(hits))
                self._send_json_response(200, {'suggestions': suggestions, 'total_words': len(suggestions)})
            except Exception as e:
                self._send_json_response(500, {'error': f'Suggestions retrieval failed: {str(e)}'})
            return

        # 6. Granular: Automated Humanizer & Diff API
        if path == '/api/humanize':
            data, err = self._read_json_body()
            if err:
                code = 413 if '25MB' in err else 400
                self._send_json_response(code, {'error': err})
                return

            try:
                raw_text = data.get('text', '')
                mode = data.get('mode', 'general')
                randomize = data.get('randomize', True)
                soften_em_dashes = data.get('soften_em_dashes', False)

                hits = audit(raw_text, mode=mode)
                cleaned_text, diff_output = humanize_text(raw_text, hits, soften_em_dashes=soften_em_dashes, randomize=randomize)
                self._send_json_response(200, {
                    'cleaned_text': cleaned_text,
                    'diff': diff_output
                })
            except Exception as e:
                self._send_json_response(500, {'error': f'Humanization failed: {str(e)}'})
            return

        # 7. Document Upload API (.docx, .pdf, .tex, .md, .txt, .zip, etc.)
        if path == '/api/upload':
            try:
                content_type = self.headers.get('Content-Type', '')
                if 'multipart/form-data' not in content_type:
                    err_resp = json.dumps({'error': 'Expected multipart/form-data'}).encode('utf-8')
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(err_resp)))
                    self.end_headers()
                    self.wfile.write(err_resp)
                    return

                length = int(self.headers.get('Content-Length', 0))
                if length > MAX_PAYLOAD_SIZE:
                    err_resp = json.dumps({'error': 'File upload exceeds maximum limit of 25MB.'}).encode('utf-8')
                    self.send_response(413)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(err_resp)))
                    self.end_headers()
                    self.wfile.write(err_resp)
                    return

                raw_body = self.rfile.read(length)

                # Construct email message for clean multipart parsing
                header_bytes = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode('latin1')
                msg = email.message_from_bytes(header_bytes + raw_body)

                filename = "document.txt"
                file_bytes = b""

                for part in msg.walk():
                    if part.get_filename():
                        filename = part.get_filename()
                        file_bytes = part.get_payload(decode=True)
                        break

                if not file_bytes:
                    err_resp = json.dumps({'error': 'No file content found in upload.'}).encode('utf-8')
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(err_resp)))
                    self.end_headers()
                    self.wfile.write(err_resp)
                    return

                extracted_text = extract_text_from_file(filename, file_bytes)

                resp_bytes = json.dumps({'filename': filename, 'text': extracted_text}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(resp_bytes)))
                self.end_headers()
                self.wfile.write(resp_bytes)
            except Exception as e:
                err_resp = json.dumps({'error': f'File extraction failed: {str(e)}'}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err_resp)))
                self.end_headers()
                self.wfile.write(err_resp)
            return

        # 8. Novel Feature 1: Token Watermark Z-Score Analyzer API
        if path == '/api/features/token-watermark':
            data, err = self._read_json_body()
            if err:
                code = 413 if '25MB' in err else 400
                self._send_json_response(code, {'error': err})
                return

            try:
                raw_text = data.get('text', '')
                result = detect_synthetic_token_watermark(raw_text)
                self._send_json_response(200, result)
            except Exception as e:
                self._send_json_response(500, {'error': f'Token watermark analysis failed: {str(e)}'})
            return

        # 9. Novel Feature 2: Model Provenance Fingerprinter API
        if path == '/api/features/provenance':
            data, err = self._read_json_body()
            if err:
                code = 413 if '25MB' in err else 400
                self._send_json_response(code, {'error': err})
                return

            try:
                raw_text = data.get('text', '')
                result = detect_model_provenance(raw_text)
                self._send_json_response(200, result)
            except Exception as e:
                self._send_json_response(500, {'error': f'Model provenance analysis failed: {str(e)}'})
            return

        # 10. Novel Feature 3: Citation & Hallucination Auditor API
        if path == '/api/features/citations':
            data, err = self._read_json_body()
            if err:
                code = 413 if '25MB' in err else 400
                self._send_json_response(code, {'error': err})
                return

            try:
                raw_text = data.get('text', '')
                result = audit_citations(raw_text)
                self._send_json_response(200, result)
            except Exception as e:
                self._send_json_response(500, {'error': f'Citation audit failed: {str(e)}'})
            return

        # 11. Novel Feature 4: Cross-Language Translation Artifact Detector API
        if path == '/api/features/translation-artifacts':
            data, err = self._read_json_body()
            if err:
                code = 413 if '25MB' in err else 400
                self._send_json_response(code, {'error': err})
                return

            try:
                raw_text = data.get('text', '')
                result = detect_translation_artifacts(raw_text)
                self._send_json_response(200, result)
            except Exception as e:
                self._send_json_response(500, {'error': f'Translation artifact detection failed: {str(e)}'})
            return

        # 12. Novel Feature 5: Local N-Gram Glider & Perplexity Profiler API
        if path == '/api/features/ngram-profile':
            data, err = self._read_json_body()
            if err:
                code = 413 if '25MB' in err else 400
                self._send_json_response(code, {'error': err})
                return

            try:
                raw_text = data.get('text', '')
                result = profile_ngrams_and_perplexity(raw_text)
                self._send_json_response(200, result)
            except Exception as e:
                self._send_json_response(500, {'error': f'N-gram profiling failed: {str(e)}'})
            return

        self.send_error(404, "Unknown API endpoint")

def get_local_ip():
    """Detects primary local network IP address for LAN access."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable; just selects outbound interface
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Multi-threaded TCP server to handle simultaneous LAN and browser requests without blocking."""
    daemon_threads = True
    allow_reuse_address = True

def run_server(port=None, host=None, open_browser=True):
    """Starts the GhostTrace web server and opens the browser."""
    port = port if port is not None else DEFAULT_PORT
    host = host if host is not None else DEFAULT_HOST
    handler = GhostTraceHandler
    with ThreadedTCPServer((host, port), handler) as httpd:
        local_url = f"http://localhost:{port}"
        lan_ip = get_local_ip()
        lan_url = f"http://{lan_ip}:{port}"

        print(f"\n" + "-" * 50)
        print(f"  GhostTrace Web Interface & API")
        print(f"  * Local Web App:   {local_url}")
        print(f"  * Swagger UI:      {local_url}/docs")
        if host in ["0.0.0.0", ""]:
            print(f"  * LAN Access:      {lan_url}")
        print(f"  * Privacy:         100% Offline (Zero External Calls)")
        print(f"  Press Ctrl+C to stop the server.")
        print("-" * 50 + "\n")

        if open_browser:
            webbrowser.open(local_url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down GhostTrace server...")

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    run_server(port=port)
