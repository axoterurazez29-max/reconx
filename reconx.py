#!/usr/bin/env python3
"""
ReconX - Modular Reconnaissance Framework
Made by Kyoraku
License: MIT
"""

import sys
import os
import json
from datetime import datetime

from core import utils
from core.runner import Runner
from core import progress as ui
from core.reporter import Reporter

VERSION = "1.0.0"
AUTHOR = "Kyoraku"

BANNER = r"""
 ____                     __  __
|  _ \ ___  ___ ___  _ __ \ \/ /
| |_) / _ \/ __/ _ \| '_ \ \  /
|  _ <  __/ (_| (_) | | | |/  \
|_| \_\___|\___\___/|_| |_/_/\_\
"""

MODULES_REGISTRY = {
    "subdomain": ("modules.subdomain", "SubdomainModule"),
    "portscan":  ("modules.portscan",  "PortScanModule"),
    "webprobe":  ("modules.webprobe",  "WebProbeModule"),
    "dirbrute":  ("modules.dirbrute",  "DirBruteModule"),
    "vulnscan":  ("modules.vulnscan",  "VulnScanModule"),
    "osint":     ("modules.osint",     "OSINTModule"),
}


def print_startup_banner():
    from rich.panel import Panel
    from rich.align import Align
    from rich.text import Text

    ui.console.print(f"[cyan]{BANNER}[/cyan]")

    brand = Text()
    brand.append("⚡ ", style="bold yellow")
    brand.append("Tools made by ", style="white")
    brand.append(AUTHOR, style="bold magenta")
    brand.append(" 🛡️", style="bold yellow")

    info_line = Text()
    info_line.append(f"ReconX v{VERSION}", style="bold cyan")
    info_line.append("  •  ", style="dim")
    info_line.append("Modular Reconnaissance Framework", style="white")

    content = Align.center(
        Text.assemble(brand, "\n", info_line),
        vertical="middle"
    )

    ui.console.print(
        Panel(content, border_style="magenta", padding=(1, 4))
    )
    ui.console.print()


def parse_arguments():
    import argparse

    parser = argparse.ArgumentParser(
        prog="reconx",
        description=f"ReconX v{VERSION} — Modular Reconnaissance Framework (by {AUTHOR})",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 reconx.py -t example.com --all\n"
            "  python3 reconx.py -t example.com -m subdomain,portscan\n"
            "  python3 reconx.py -t 192.168.1.1 -m portscan\n"
        )
    )

    parser.add_argument("-t", "--target", required=True, help="Target domain or IP")
    parser.add_argument("-m", "--modules", help="Comma-separated module list")
    parser.add_argument("--all", action="store_true", help="Run all modules")
    parser.add_argument("--list-modules", action="store_true", help="List modules")
    parser.add_argument("-o", "--output-dir", default=None, help="Custom output folder name")
    parser.add_argument("--threads", type=int, default=50, help="Thread count (default: 50)")
    parser.add_argument("--timeout", type=int, default=300, help="Per-module timeout (default: 300s)")
    parser.add_argument("--ports", default="1-1000", help="Port range for portscan (default: 1-1000)")
    parser.add_argument("--skip-tool-check", action="store_true", help="Skip external tool verification")
    parser.add_argument("--no-report", action="store_true", help="Skip HTML report generation")
    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    parser.add_argument("-v", "--version", action="version", version=f"ReconX {VERSION} by {AUTHOR}")

    return parser.parse_args()


def resolve_modules(args):
    if args.list_modules:
        ui.header("Available Modules")
        for key in MODULES_REGISTRY.keys():
            ui.console.print(f"  [cyan]•[/cyan] {key}")
        sys.exit(0)

    if args.all:
        return list(MODULES_REGISTRY.keys())

    if not args.modules:
        ui.error("No modules selected.")
        ui.info(f"Use --all or -m with one of: {', '.join(MODULES_REGISTRY.keys())}")
        sys.exit(1)

    selected = [m.strip() for m in args.modules.split(",") if m.strip()]
    invalid = [m for m in selected if m not in MODULES_REGISTRY]

    if invalid:
        ui.error(f"Unknown module(s): {', '.join(invalid)}")
        ui.info(f"Available: {', '.join(MODULES_REGISTRY.keys())}")
        sys.exit(1)

    return selected


def create_output_dir(target, custom_name=None):
    safe = utils.sanitize_name(target)
    ts = utils.timestamp()
    dirname = custom_name if custom_name else f"{safe}_{ts}"
    base = os.path.join("output", dirname)
    utils.ensure_dir(os.path.join(base, "raw"))
    return base


def verify_target(target):
    if utils.is_valid_ip(target):
        return "ip"
    if utils.is_valid_domain(target):
        if utils.resolve_target(target):
            return "domain"
        ui.warn(f"Domain '{target}' did not resolve. Continuing anyway.")
    return "unknown"


def load_module(key):
    import importlib
    module_path, class_name = MODULES_REGISTRY[key]
    try:
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        return cls
    except (ImportError, AttributeError):
        return None


def main():
    args = parse_arguments()

    if not args.no_color:
        print_startup_banner()

    modules = resolve_modules(args)
    target_type = verify_target(args.target)
    output_dir = create_output_dir(args.target, args.output_dir)

    ui.info(f"Target      : [bold]{args.target}[/bold] ({target_type})")
    ui.info(f"Modules     : [bold]{', '.join(modules)}[/bold]")
    ui.info(f"Output dir  : [bold]{output_dir}[/bold]")
    ui.info(f"Threads     : {args.threads}")
    ui.info(f"Timeout     : {args.timeout}s")

    runner = Runner(verbose=False)
    module_summaries = []
    all_results = {}

    ui.header("Running Modules")

    for key in modules:
        cls = load_module(key)
        if cls is None:
            ui.warn(f"Module '{key}' not yet implemented — skipping")
            module_summaries.append({
                "module": key,
                "found": 0,
                "duration": 0.0,
                "status": "skip"
            })
            continue

        init_kwargs = {
            "runner": runner,
            "threads": args.threads,
            "timeout": args.timeout,
        }
        if key == "portscan":
            init_kwargs["ports"] = args.ports

        module = cls(**init_kwargs)
        summary = module.execute(args.target, output_dir)

        module_summaries.append({
            "module": summary["key"],
            "found": summary["found"],
            "duration": summary["duration"],
            "status": summary["status"]
        })
        all_results[key] = summary["results"]

    ui.header("Results")
    ui.show_module_summary(module_summaries)

    combined_path = os.path.join(output_dir, "results.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump({
            "target": args.target,
            "target_type": target_type,
            "scan_time": utils.human_timestamp(),
            "framework": f"ReconX v{VERSION}",
            "author": AUTHOR,
            "modules": module_summaries,
            "results": all_results
        }, f, indent=2)

    ui.success(f"Results saved: {combined_path}")

    if not args.no_report:
        try:
            reporter = Reporter()
            report_path = reporter.generate(
                target=args.target,
                target_type=target_type,
                results=all_results,
                output_dir=output_dir,
            )
            ui.print_report_path(report_path)
        except Exception as e:
            ui.error(f"Report generation failed: {e}")

    total_found = sum(s["found"] for s in module_summaries)
    ui.console.print()
    ui.console.print(
        f"[bold green]Total findings:[/bold green] [yellow]{total_found}[/yellow]"
    )
    ui.console.print()
    ui.console.print("[dim]─────────────────────────────────────────────[/dim]")
    ui.console.print(f"[dim]  Powered by [bold magenta]{AUTHOR}[/bold magenta][/dim]")
    ui.console.print("[dim]─────────────────────────────────────────────[/dim]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        ui.console.print()
        ui.warn("Interrupted by user.")
        sys.exit(0)
