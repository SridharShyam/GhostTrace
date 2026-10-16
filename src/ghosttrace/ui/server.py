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

# Maximum upload and audit payload ceiling (25 MB) to prevent OOM/DoS
MAX_PAYLOAD_SIZE = 25 * 1024 * 1024

class GhostTraceHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving UI templates and REST API endpoints."""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Serve clean Unstop Light Theme HTML & Static Assets directly
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
            try:
                length = int(self.headers.get('Content-Length', 0))
                if length > MAX_PAYLOAD_SIZE:
                    err_resp = json.dumps({'error': 'Payload exceeds maximum limit of 25MB.'}).encode('utf-8')
                    self.send_response(413)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(err_resp)))
                    self.end_headers()
                    self.wfile.write(err_resp)
                    return

                body = self.rfile.read(length).decode('utf-8', errors='replace')
                data = json.loads(body) if body.strip() else {}
                raw_text = data.get('text', '')
                mode = data.get('mode', 'general')

                # Parse depending on mode/format
                parsed_text = raw_text
                if mode == 'academic' and ('\\section' in raw_text or '\\begin' in raw_text or '\\cite' in raw_text):
                    parsed_text = latex_prose(raw_text)

                hits = audit(parsed_text, mode=mode)
                burst = analyze_burstiness(parsed_text)
                word_count = len(parsed_text.split())
                score, total_vocab, density_penalty, total_phrases = calculate_score(hits, word_count=word_count, burst=burst)
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
            except Exception as e:
                err_resp = json.dumps({'error': f'Audit processing failed: {str(e)}'}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(err_resp)))
                self.end_headers()
                self.wfile.write(err_resp)
            return

        # 2. Document Upload API (.docx, .pdf, .tex, .md, .txt, .zip, etc.)
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

def run_server(port=7860, host="127.0.0.1", open_browser=True):
    """Starts local or shared LAN GhostTrace Web UI server."""
    handler = GhostTraceHandler
    with ThreadedTCPServer((host, port), handler) as httpd:
        local_url = f"http://localhost:{port}"
        lan_ip = get_local_ip()
        lan_url = f"http://{lan_ip}:{port}"

        print(f"\n=======================================================")
        print(f"  GhostTrace Zero-Trust Local & Team Hub")
        print(f"  * Local Access:     {local_url}")
        if host in ["0.0.0.0", ""]:
            print(f"  * Team / LAN Access: {lan_url}  (Colleagues on same Wi-Fi/LAN)")
        print(f"  * Privacy Status:   100% Offline (Zero Cloud Telemetry)")
        print(f"  Press Ctrl+C to stop the server")
        print(f"=======================================================\n")

        if open_browser:
            webbrowser.open(local_url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down GhostTrace Web UI server...")

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 7860
    run_server(port=port)
