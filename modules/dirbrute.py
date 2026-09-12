#!/usr/bin/env python3
"""
ReconX - Directory Brute-force Module
Wraps: ffuf, gobuster
"""

import os
import json

from core.base import BaseModule
from core import utils
from core import progress as ui


DEFAULT_WORDLIST_PATHS = [
    os.path.expanduser("~/.wordlists/wordlist.txt"),
    os.path.expanduser("~/wordlists/wordlist.txt"),
    "/data/data/com.termux/files/home/.wordlists/wordlist.txt",
]


class DirBruteModule(BaseModule):
    name = "Directory Brute-force"
    key = "dirbrute"
    required_tools = []
    description = "Discover directories and files."

    def _has(self, tool):
        return utils.tool_exists(tool)

    def _find_wordlist(self):
        for path in DEFAULT_WORDLIST_PATHS:
            if os.path.exists(path):
                return path
        return None

    def _get_live_urls(self, output_dir, target):
        """Try to read live URLs from previous webprobe output."""
        candidates = [
            os.path.join(output_dir, "raw", "httpx.txt"),
        ]

        urls = []
        for path in candidates:
            if os.path.exists(path):
                for line in utils.read_lines(path):
                    url = line.split()[0]
                    if url.startswith(("http://", "https://")):
                        urls.append(url)
        return urls

    def _run_ffuf(self, base_url, wordlist, output_dir):
        ui.info(f"  → Running ffuf on {base_url}...")

        output_file = os.path.join(
            output_dir, "raw", "ffuf_" + utils.sanitize_name(base_url) + ".json"
        )
        utils.ensure_dir(os.path.dirname(output_file))

        args = [
            "-u", base_url.rstrip("/") + "/FUZZ",
            "-w", wordlist,
            "-mc", "200,204,301,302,307,401,403",
            "-t", str(min(self.threads, 40)),
            "-s",
            "-of", "json",
            "-o", output_file,
        ]

        result = self.runner.run("ffuf", args, timeout=self.timeout)

        if not os.path.exists(output_file):
            if result.stderr:
                ui.warn(f"    ffuf: {result.stderr[:100]}")
            return []

        try:
            with open(output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return []

        results = []
        for item in data.get("results", []):
            results.append({
                "url": item.get("url", ""),
                "status": item.get("status", 0),
                "length": item.get("length", 0),
                "words": item.get("words", 0),
                "lines": item.get("lines", 0)
            })

        return results

    def _run_gobuster(self, base_url, wordlist, output_dir):
        if not self._has("gobuster"):
            return []

        ui.info(f"  → Running gobuster on {base_url}...")

        output_file = os.path.join(
            output_dir, "raw", "gobuster_" + utils.sanitize_name(base_url) + ".txt"
        )
        utils.ensure_dir(os.path.dirname(output_file))

        args = [
            "dir",
            "-u", base_url,
            "-w", wordlist,
            "-q",
            "-t", str(min(self.threads, 40)),
            "-o", output_file,
        ]

        result = self.runner.run("gobuster", args, timeout=self.timeout)

        if not os.path.exists(output_file):
            return []

        results = []
        for line in utils.read_lines(output_file):
            parts = line.split()
            if len(parts) >= 2 and parts[1].startswith("("):
                path = parts[0]
                status_str = parts[1].strip("()")
                try:
                    status = int(status_str)
                except ValueError:
                    status = 0
                results.append({
                    "url": base_url.rstrip("/") + "/" + path.lstrip("/"),
                    "status": status,
                    "length": 0,
                    "words": 0,
                    "lines": 0
                })

        return results

    def run(self, target, output_dir, **kwargs):
        ui.info(f"  Target: {target}")

        wordlist = self._find_wordlist()
        if not wordlist:
            ui.warn("  No wordlist found. Create ~/.wordlists/wordlist.txt")
            return []

        ui.info(f"  Wordlist: {wordlist}")

        base_urls = self._get_live_urls(output_dir, target)
        if not base_urls:
            base_urls = ["https://" + target, "http://" + target]
            ui.info(f"  Using default base URLs: {', '.join(base_urls)}")
        else:
            base_urls = base_urls[:3]
            ui.info(f"  Testing {len(base_urls)} URL(s)")

        all_findings = []

        for base_url in base_urls:
            if self._has("ffuf"):
                res = self._run_ffuf(base_url, wordlist, output_dir)
                all_findings.extend(res)
            elif self._has("gobuster"):
                res = self._run_gobuster(base_url, wordlist, output_dir)
                all_findings.extend(res)
            else:
                ui.warn("  Neither ffuf nor gobuster installed — skipping")
                return []

        seen = set()
        unique = []
        for item in all_findings:
            key = item["url"]
            if key not in seen:
                seen.add(key)
                unique.append(item)

        unique = sorted(unique, key=lambda x: (x["status"], x["url"]))

        if unique:
            ui.info(f"  → Directories found: {len(unique)}")
            for f in unique[:10]:
                ui.console.print(
                    f"      [green]{f['status']:>3}[/green]  [cyan]{f['url']}[/cyan]"
                )
            if len(unique) > 10:
                ui.info(f"      ... and {len(unique) - 10} more")

        return unique
