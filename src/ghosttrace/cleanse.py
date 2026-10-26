#!/usr/bin/env python3
"""Cross-platform automated cleanser & second-pass humanizer for GhostTrace.

Takes an AI draft, prompts an alternate model family or local LLM (via CLI, API, or interactive prompt),
and scrubs AI tells while preserving facts, technical arguments, and citations.

Works seamlessly on Windows, macOS, and Linux without bash or unix dependencies.
"""

import argparse
import os
import shutil
import subprocess
import sys

EDITORIAL_PROMPT = """You are an exacting editor cleansing this text of AI writing tells and promotional fluff.

Your task:
1. Strip all conversational filler and empty hype (e.g. "game-changing", "seamless", "delve into", "in today's fast-paced world", "not just X, but Y").
2. For academic copy: keep legitimate scientific terms (like "robust control" or "convex optimization"), but remove unverified superlative claims ("groundbreaking", "unprecedented accuracy").
3. Preserve all facts, mathematical formulas, LaTeX markup, citations, and technical statements exactly.
4. Vary sentence length naturally. Mix short, direct statements with compound sentences.
5. Do NOT invent new statistics, customer counts, or citations.

Format your response as:
[CLEANSED DRAFT]
(your rewritten text here)

<<<GHOSTTRACE-NOTES>>>
(up to 5 bullet points explaining substantive cuts and fixes)
"""

def cleanse_with_command(cmd, input_text):
    """Run an external CLI command (e.g. claude, gpt, ollama) with the prompt and draft."""
    full_prompt = f"{EDITORIAL_PROMPT}\n\nDraft to cleanse:\n{input_text}"
    try:
        proc = subprocess.run(
            cmd,
            input=full_prompt,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            shell=True
        )
        if proc.returncode != 0:
            print(f"[!] Warning: Command failed with code {proc.returncode}:\n{proc.stderr}", file=sys.stderr)
            return None, None
        
        output = proc.stdout
        notes = ""
        if "<<<GHOSTTRACE-NOTES>>>" in output:
            parts = output.split("<<<GHOSTTRACE-NOTES>>>", 1)
            output = parts[0].replace("[CLEANSED DRAFT]", "").strip()
            notes = parts[1].strip()
        else:
            output = output.replace("[CLEANSED DRAFT]", "").strip()
        return output, notes
    except Exception as e:
        print(f"[!] Error invoking command: {e}", file=sys.stderr)
        return None, None

def main():
    parser = argparse.ArgumentParser(description="GhostTrace Cross-Model Cleanser")
    parser.add_argument("file", help="Draft file to cleanse (.txt, .md, .tex)")
    parser.add_argument("--model-cli", help="Command to run model CLI (e.g., 'ollama run llama3', 'claude', 'gpt')", default=None)
    parser.add_argument("--output", "-o", help="Output destination for cleansed file", default=None)
    parser.add_argument("--notes", "-n", help="Destination for change notes", default=None)
    parser.add_argument("--print-prompt", action="store_true", help="Print the standalone prompt to paste into any web AI chat")

    args = parser.parse_args()

    if args.print_prompt:
        if os.path.exists(args.file):
            draft = open(args.file, encoding='utf-8', errors='replace').read()
            print(f"{EDITORIAL_PROMPT}\n\nDraft to cleanse:\n{draft}")
        else:
            print(EDITORIAL_PROMPT)
        return

    if not os.path.exists(args.file):
        sys.exit(f"ghosttrace cleanse: file not found: {args.file}")

    draft = open(args.file, encoding='utf-8', errors='replace').read()

    # Determine command
    cmd = args.model_cli
    if not cmd:
        from ghosttrace.config import DEFAULT_CLEANSE_CMD
        if DEFAULT_CLEANSE_CMD and shutil.which(DEFAULT_CLEANSE_CMD.split()[0]):
            cmd = DEFAULT_CLEANSE_CMD

    if not cmd:
        # Detect available CLIs in PATH
        for candidate in ["ollama", "claude", "gpt", "aichat"]:
            if shutil.which(candidate):
                if candidate == "ollama":
                    cmd = "ollama run llama3"
                else:
                    cmd = candidate
                break

    if not cmd:
        print("[!] No supported AI CLI found automatically on your system (ollama, claude, gpt).", file=sys.stderr)
        print("    Printing the complete editorial prompt and draft below so you can paste it into Claude, ChatGPT, or Gemini:\n", file=sys.stderr)
        print(f"{EDITORIAL_PROMPT}\n\nDraft to cleanse:\n{draft}")
        sys.exit(127)

    print(f"[*] Running second-pass humanizer via: {cmd}...", file=sys.stderr)
    cleansed, notes = cleanse_with_command(cmd, draft)

    if cleansed:
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(cleansed)
            print(f"[+] Cleansed draft written to: {args.output}", file=sys.stderr)
        else:
            print(cleansed)

        if notes:
            if args.notes:
                with open(args.notes, "w", encoding="utf-8") as f:
                    f.write(notes)
            else:
                print(f"\nEditorial Change Notes:\n{notes}", file=sys.stderr)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
