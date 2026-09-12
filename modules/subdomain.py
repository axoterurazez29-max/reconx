#!/usr/bin/env python3
"""
ReconX - Subdomain Enumeration Module
Wraps: subfinder, assetfinder, dnsx
"""

import os

from core.base import BaseModule
from core import utils
from core import progress as ui


class SubdomainModule(BaseModule):
    name = "Subdomain Enumeration"
    key = "subdomain"
    required_tools = ["subfinder", "assetfinder", "dnsx"]
    description = "Enumerate subdomains using multiple passive sources."

    def _run_subfinder(self, target, output_dir):
        ui.info("  → Running subfinder...")
        result = self.runner.run(
            "subfinder",
            ["-d", target, "-silent", "-all"],
            timeout=self.timeout
        )

        lines = [ln.strip() for ln in result.lines if ln.strip()]
        self.save_raw(output_dir, "subfinder.txt", "\n".join(lines))

        if result.success:
            ui.success(f"    subfinder: {len(lines)} subdomain(s)")
        else:
            ui.warn(f"    subfinder failed: {result.stderr[:80]}")

        return lines

    def _run_assetfinder(self, target, output_dir):
        ui.info("  → Running assetfinder...")
        result = self.runner.run(
            "assetfinder",
            ["--subs-only", target],
            timeout=self.timeout
        )

        lines = [ln.strip() for ln in result.lines if ln.strip()]
        self.save_raw(output_dir, "assetfinder.txt", "\n".join(lines))

        if result.success:
            ui.success(f"    assetfinder: {len(lines)} subdomain(s)")
        else:
            ui.warn(f"    assetfinder failed: {result.stderr[:80]}")

        return lines

    def _filter_target(self, entries, target):
        cleaned = []
        for e in entries:
            e = e.strip().lower()
            if not e:
                continue
            if e.startswith("*."):
                e = e[2:]
            if e.endswith(target) and e != target:
                cleaned.append(e)
        return cleaned

    def _resolve_dns(self, subdomains, output_dir):
        if not subdomains:
            return []

        ui.info(f"  → Resolving {len(subdomains)} subdomain(s) via dnsx...")

        input_data = "\n".join(subdomains)

        result = self.runner.run(
            "dnsx",
            ["-silent", "-a", "-resp"],
            timeout=self.timeout,
            stdin_data=input_data
        )

        resolved = []
        for line in result.lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) >= 2:
                subdomain = parts[0]
                ip = parts[-1]
            else:
                subdomain = line
                ip = ""

            resolved.append({
                "subdomain": subdomain,
                "ip": ip
            })

        self.save_raw(
            output_dir,
            "dnsx_resolved.txt",
            "\n".join(f"{r['subdomain']} {r['ip']}" for r in resolved)
        )

        ui.success(f"    dnsx: {len(resolved)} resolved")

        return resolved

    def run(self, target, output_dir, **kwargs):
        ui.info(f"  Target: {target}")

        collected = []

        sf = self._run_subfinder(target, output_dir)
        collected.extend(sf)

        af = self._run_assetfinder(target, output_dir)
        collected.extend(af)

        collected = self._filter_target(collected, target)
        collected = utils.dedupe(collected)

        ui.info(f"  → Unique subdomains: {len(collected)}")

        if not collected:
            return []

        resolved = self._resolve_dns(collected, output_dir)

        return resolved
