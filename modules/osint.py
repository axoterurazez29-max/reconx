#!/usr/bin/env python3
"""
ReconX - OSINT Module
Wraps: whois, dig
"""

import os
import re
import socket

from core.base import BaseModule
from core import utils
from core import progress as ui


class OSINTModule(BaseModule):
    name = "OSINT Gathering"
    key = "osint"
    required_tools = []
    description = "Gather WHOIS, DNS, and network information."

    def _has(self, tool):
        return utils.tool_exists(tool)

    def _run_whois(self, target, output_dir):
        if not self._has("whois"):
            ui.warn("    whois not installed — skipping")
            return {}

        ui.info("  → Running whois...")
        result = self.runner.run("whois", [target], timeout=30)

        self.save_raw(output_dir, "whois.txt", result.stdout)

        if not result.success:
            ui.warn(f"    whois failed: {result.stderr[:80]}")
            return {}

        info = {}
        patterns = {
            "registrar": r"Registrar:\s*(.+)",
            "creation_date": r"Creation Date:\s*(.+)",
            "expiry_date": r"Registry Expiry Date:\s*(.+)",
            "updated_date": r"Updated Date:\s*(.+)",
            "name_servers": r"Name Server:\s*(.+)",
            "status": r"Domain Status:\s*(.+)",
            "org": r"Registrant Organization:\s*(.+)",
            "country": r"Registrant Country:\s*(.+)",
        }

        for key, pattern in patterns.items():
            matches = re.findall(pattern, result.stdout, re.IGNORECASE)
            if matches:
                info[key] = matches if len(matches) > 1 else matches[0]

        return info

    def _run_dig(self, target, output_dir):
        if not self._has("dig"):
            ui.warn("    dig not installed — skipping")
            return {}

        records = {}
        for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]:
            result = self.runner.run(
                "dig",
                ["+short", target, rtype],
                timeout=15
            )
            lines = [ln.strip() for ln in result.lines if ln.strip()]
            if lines:
                records[rtype] = lines

        self.save_raw(
            output_dir,
            "dns_records.txt",
            "\n".join(f"{k}: {', '.join(v)}" for k, v in records.items())
        )

        return records

    def _resolve_ip(self, target):
        try:
            return socket.gethostbyname(target)
        except Exception:
            return None

    def run(self, target, output_dir, **kwargs):
        ui.info(f"  Target: {target}")

        findings = {
            "target": target,
            "ip": self._resolve_ip(target),
            "whois": {},
            "dns": {}
        }

        whois_info = self._run_whois(target, output_dir)
        if whois_info:
            findings["whois"] = whois_info
            ui.success(f"    whois: {len(whois_info)} field(s) collected")

        dns_info = self._run_dig(target, output_dir)
        if dns_info:
            findings["dns"] = dns_info
            total_records = sum(len(v) for v in dns_info.values())
            ui.success(f"    dns: {total_records} record(s)")

        if findings["ip"]:
            ui.info(f"  → Resolved IP: {findings['ip']}")

        return [findings]

