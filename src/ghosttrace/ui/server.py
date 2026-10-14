#!/usr/bin/env python3
"""Standard Library HTTP Server backend for GhostTrace Web UI."""

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
    get_suggestions,
)
from ghosttrace.ui.extractor import extract_text_from_file

UI_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(UI_DIR, "static")
TEMPLATES_DIR = os.path.join(UI_DIR, "templates")

class GhostTraceHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving UI templates and REST API endpoints."""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ['/', '/index.html']:
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

        self.send_error(404, "File not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. Audit Live Text API
        if path == '/api/audit':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            data = json.loads(body)
            raw_text = data.get('text', '')
            mode = data.get('mode', 'general')

            # Parse depending on mode/format
            parsed_text = raw_text
            if mode == 'academic' and ('\\section' in raw_text or '\\begin' in raw_text or '\\cite' in raw_text):
                parsed_text = latex_prose(raw_text)

            hits = audit(parsed_text, mode=mode)
            burst = analyze_burstiness(parsed_text)
            word_count = len(parsed_text.split())
            score, total_vocab, density_penalty, total_phrases = calculate_score(hits, word_count=word_count)
            watermarks = detect_watermarks(raw_text)
            suggestions = dict(get_suggestions(hits))

            response = {
                'mode': mode,
                'word_count': word_count,
                'score': score,
                'hits': hits,
                'burstiness': burst,
                'watermarks': watermarks,
                'suggestions': suggestions,
            }

            resp_bytes = json.dumps(response).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # 2. Document Upload API (.docx, .pdf, .tex, .md, .txt)
        if path == '/api/upload':
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                self.send_error(400, "Expected multipart/form-data")
                return

            length = int(self.headers.get('Content-Length', 0))
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
                self.send_error(400, "No file found in multipart upload")
                return

            extracted_text = extract_text_from_file(filename, file_bytes)

            resp_bytes = json.dumps({'filename': filename, 'text': extracted_text}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        self.send_error(404, "Unknown API endpoint")

def run_server(port=7860, open_browser=True):
    """Starts local GhostTrace Web UI server."""
    handler = GhostTraceHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}"
        print(f"\n=======================================================")
        print(f"  GhostTrace Web UI is running at: {url}")
        print(f"  Press Ctrl+C to stop the server")
        print(f"=======================================================\n")
        if open_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down GhostTrace Web UI server...")

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 7860
    run_server(port=port)
