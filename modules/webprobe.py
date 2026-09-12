#!/usr/bin/env python3
"""
ReconX - Web Probing Module
Wraps: httpx (ProjectDiscovery)
"""

import os

from core.base import BaseModule
from core import utils
from core import progress as ui


class WebProbeModule(BaseModule):
    name = "Web Probing"
    key = "webprobe"
    required_tools = ["httpx"]
    description = "Probe live web servers using httpx."

    def _read_subdomains(self, output_dir):
        """Try to read subdomains from previous subdomain module output."""
        candidates = [
            os.path.join(output_dir, "raw", "dnsx_resolved.txt"),
            os.path.join(output_dir, "raw", "subfinder.txt"),
            os.path.join(output_dir, "raw", "assetfinder.txt"),
        ]

        subs = []
        for path in candidates:
            if os.path.exists(path):
                for line in utils.read_lines(path):
                    parts = line.split()
                    if parts:
                        subs.append(parts[0])
        return utils.dedupe(subs)

    def _write_input(self, output_dir, hosts):
        path = os.path.join(output_dir, "raw", "webprobe_input.txt")
        utils.write_file(path, "\n".join(hosts))
        return path

    def run(self, target, output_dir, **kwargs):
        ui.info(f"  Target: {target}")

        hosts = self._read_subdomains(output_dir)

        if not hosts:
            ui.warn("  No subdomains found from previous step — using target only")
            hosts = [target]

        ui.info(f"  → Probing {len(hosts)} host(s)...")

        self._write_input(output_dir, hosts)

        input_data = "\n".join(hosts)

        args = [
            "-silent",
            "-status-code",
            "-title",
            "-tech-detect",
            "-server",
            "-no-color",
        ]

        result = self.runner.run(
            "httpx",
            args,
            timeout=self.timeout,
            stdin_data=input_data
        )

        self.save_raw(output_dir, "httpx.txt", result.stdout)
        self.save_raw(output_dir, "httpx.stderr", result.stderr)

        if not result.success:
            ui.warn(f"    httpx failed: {result.stderr[:100]}")

        findings = []
        for line in result.lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if not parts:
                continue

            url = parts[0]
            status = None
            title = ""
            tech = ""
            server = ""

            for token in parts[1:]:
                if token.startswith("[") and token.endswith("]"):
                    content = token[1:-1]
                    if content.isdigit():
                        status = int(content)
                    elif not title:
                        title = content
                elif token.startswith("[") and "]" in token:
                    pass

            findings.append({
                "url": url,
                "status": status,
                "title": title,
                "raw": line
            })

        if findings:
            ui.info(f"  → Live hosts: {len(findings)}")
            for f in findings[:10]:
                status = f["status"] if f["status"] else "?"
                ui.console.print(
                    f"      [green]{status:>3}[/green]  [cyan]{f['url']}[/cyan]"
                )
            if len(findings) > 10:
                ui.info(f"      ... and {len(findings) - 10} more")

        return findings
