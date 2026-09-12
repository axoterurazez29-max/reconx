#!/usr/bin/env python3
"""
ReconX - Vulnerability Scanning Module
Wraps: nuclei
"""

import os
import json

from core.base import BaseModule
from core import utils
from core import progress as ui


class VulnScanModule(BaseModule):
    name = "Vulnerability Scanning"
    key = "vulnscan"
    required_tools = ["nuclei"]
    description = "Scan for known vulnerabilities using nuclei."

    def _get_targets(self, output_dir, target):
        urls = []
        candidates = [
            os.path.join(output_dir, "raw", "httpx.txt"),
        ]
        for path in candidates:
            if os.path.exists(path):
                for line in utils.read_lines(path):
                    url = line.split()[0]
                    if url.startswith(("http://", "https://")):
                        urls.append(url)

        if not urls:
            urls = ["https://" + target, "http://" + target]

        return urls[:5]

    def run(self, target, output_dir, **kwargs):
        ui.info(f"  Target: {target}")

        targets = self._get_targets(output_dir, target)
        ui.info(f"  → Scanning {len(targets)} host(s) with nuclei...")

        input_file = os.path.join(output_dir, "raw", "nuclei_input.txt")
        utils.write_file(input_file, "\n".join(targets))

        output_file = os.path.join(output_dir, "raw", "nuclei.jsonl")
        utils.ensure_dir(os.path.dirname(output_file))

        args = [
            "-l", input_file,
            "-severity", "low,medium,high,critical",
            "-silent",
            "-jsonl",
            "-o", output_file,
            "-no-color",
        ]

        result = self.runner.run("nuclei", args, timeout=self.timeout)

        self.save_raw(output_dir, "nuclei.stderr", result.stderr)

        if not os.path.exists(output_file):
            if result.stderr:
                ui.warn(f"    nuclei: {result.stderr[:100]}")
            return []

        findings = []
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                    except Exception:
                        continue

                    info = item.get("info", {})
                    findings.append({
                        "template": item.get("template-id", ""),
                        "name": info.get("name", ""),
                        "severity": info.get("severity", "info"),
                        "url": item.get("matched-at", item.get("host", "")),
                        "type": item.get("type", "")
                    })
        except Exception:
            return []

        if findings:
            ui.info(f"  → Vulnerabilities: {len(findings)}")
            for f in findings[:10]:
                ui.console.print(
                    f"      [red]{f['severity']:>8}[/red]  "
                    f"[cyan]{f['name'][:40]}[/cyan]  {f['url'][:50]}"
                )
            if len(findings) > 10:
                ui.info(f"      ... and {len(findings) - 10} more")

        return findings
