#!/usr/bin/env python3
"""
ReconX - HTML Report Generator
Uses Jinja2 to render a clean white-background report.
"""

import os
import json
from datetime import datetime

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import utils
from . import progress as ui


VERSION = "1.0.0"
AUTHOR = "Kyoraku"


class Reporter:
    def __init__(self, template_dir="templates"):
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _count_by_module(self, results):
        counts = {
            "subdomain": 0,
            "portscan": 0,
            "webprobe": 0,
            "dirbrute": 0,
            "vulnscan": 0,
            "osint": 0,
        }
        for key, items in results.items():
            if isinstance(items, list):
                counts[key] = len(items)
            elif items:
                counts[key] = 1
        return counts

    def generate(self, target, target_type, results, output_dir, scan_time=None):
        scan_time = scan_time or utils.human_timestamp()

        counts = self._count_by_module(results)
        total = sum(counts.values())

        template = self.env.get_template("report.html")

        html = template.render(
            target=target,
            target_type=target_type,
            scan_time=scan_time,
            framework=f"ReconX v{VERSION}",
            version=VERSION,
            author=AUTHOR,
            results=results,
            counts=counts,
            total_findings=total,
        )

        report_path = os.path.join(output_dir, "report.html")
        utils.write_file(report_path, html)

        return report_path

    def generate_from_json(self, json_path, output_path=None):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        target = data.get("target", "unknown")
        target_type = data.get("target_type", "unknown")
        scan_time = data.get("scan_time", utils.human_timestamp())
        results = data.get("results", {})

        if output_path is None:
            output_path = os.path.join(os.path.dirname(json_path), "report.html")

        counts = self._count_by_module(results)
        total = sum(counts.values())

        template = self.env.get_template("report.html")
        html = template.render(
            target=target,
            target_type=target_type,
            scan_time=scan_time,
            framework=f"ReconX v{VERSION}",
            version=VERSION,
            author=AUTHOR,
            results=results,
            counts=counts,
            total_findings=total,
        )

        utils.write_file(output_path, html)
        return output_path
