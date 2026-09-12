#!/usr/bin/env python3
"""
ReconX - Port Scanning Module
Wraps: nmap
"""

import os
import re

from core.base import BaseModule
from core import utils
from core import progress as ui


COMMON_PORTS = {
    21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
    80: "http", 110: "pop3", 111: "rpcbind", 135: "msrpc",
    139: "netbios-ssn", 143: "imap", 443: "https", 445: "microsoft-ds",
    993: "imaps", 995: "pop3s", 1723: "pptp", 3306: "mysql",
    3389: "ms-wbt-server", 5432: "postgresql", 5900: "vnc",
    6379: "redis", 8080: "http-proxy", 8443: "https-alt",
}


class PortScanModule(BaseModule):
    name = "Port Scanning"
    key = "portscan"
    required_tools = ["nmap"]
    description = "Scan common TCP ports using nmap."

    def __init__(self, runner=None, threads=50, timeout=300, ports=None):
        super().__init__(runner=runner, threads=threads, timeout=timeout)
        self.ports = ports or "1-1000"

    def _run_nmap(self, target, output_dir):
        ui.info(f"  → Running nmap on {target} (ports: {self.ports})...")

        args = [
            "-p", self.ports,
            "-sT",
            "-T4",
            "-Pn",
            "--open",
            "-oX", "-",
            target
        ]

        result = self.runner.run("nmap", args, timeout=self.timeout)

        self.save_raw(output_dir, "nmap.xml", result.stdout)
        self.save_raw(output_dir, "nmap.stderr", result.stderr)

        if not result.success:
            ui.warn(f"    nmap failed: {result.stderr[:100]}")

        return result

    def _parse_xml(self, xml_text):
        findings = []

        port_pattern = re.compile(
            r'<port\s+protocol="(\w+)"\s+portid="(\d+)"[^>]*>'
            r'.*?<state\s+state="(\w+)"[^>]*/>'
            r'(?:.*?<service\s+name="([^"]*)"[^>]*?(?:product="([^"]*)")?[^>]*?(?:version="([^"]*)")?[^>]*/>)?',
            re.DOTALL
        )

        for match in port_pattern.finditer(xml_text):
            protocol = match.group(1)
            portid = int(match.group(2))
            state = match.group(3)
            service = match.group(4) or COMMON_PORTS.get(portid, "unknown")
            product = match.group(5) or ""
            version = match.group(6) or ""

            if state != "open":
                continue

            banner = " ".join(part for part in [product, version] if part).strip()

            findings.append({
                "port": portid,
                "protocol": protocol,
                "state": state,
                "service": service,
                "banner": banner
            })

        return findings

    def _filter_by_host(self, findings, target):
        return findings

    def run(self, target, output_dir, **kwargs):
        ui.info(f"  Target: {target}")

        result = self._run_nmap(target, output_dir)

        if not result.stdout:
            ui.warn("    nmap returned no output")
            return []

        findings = self._parse_xml(result.stdout)

        findings = sorted(findings, key=lambda x: x["port"])

        if findings:
            ui.info(f"  → Open ports found: {len(findings)}")
            for f in findings[:10]:
                banner = f["banner"][:40] if f["banner"] else ""
                ui.console.print(
                    f"      [green]{f['port']:>5}/tcp[/green]  "
                    f"[cyan]{f['service']:<15}[/cyan]  {banner}"
                )
            if len(findings) > 10:
                ui.info(f"      ... and {len(findings) - 10} more")

        return findings
